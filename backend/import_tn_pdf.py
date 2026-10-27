"""
Extract all institution data from tn.pdf and update the institutions table.
The PDF has: CURRENT_APPLICATION_NUMBER, INSTITUTE_NAME, INSTI_ADDRESS, INSTI_STATE, INSTI_WEBSITE
Match by: permanent_id (application number) OR institute name
"""
import sys, re
sys.path.insert(0, '.')

import pdfplumber

PDF_PATH = "C:/Users/meena/Desktop/ps22/data/tn.pdf"

print("Reading PDF...")
records = []

def clean(text):
    if not text:
        return ""
    return re.sub(r'\(cid:\d+\)', ' ', text).replace('\n', ' ').strip()

with pdfplumber.open(PDF_PATH) as pdf:
    total_pages = len(pdf.pages)
    print(f"Total pages: {total_pages}")

    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                if not row or len(row) < 2:
                    continue
                # Skip header row
                if row[0] and 'APPLICATION' in str(row[0]).upper():
                    continue
                app_no = clean(row[0]) if row[0] else ""
                name   = clean(row[1]) if len(row) > 1 and row[1] else ""
                addr   = clean(row[2]) if len(row) > 2 and row[2] else ""
                state  = clean(row[3]) if len(row) > 3 and row[3] else ""
                website= clean(row[4]) if len(row) > 4 and row[4] else ""

                if app_no and name and state:
                    records.append({
                        "app_no":  app_no,
                        "name":    name,
                        "address": addr,
                        "state":   state,
                        "website": website,
                    })

        if (i + 1) % 50 == 0:
            print(f"  Processed page {i+1}/{total_pages}, records so far: {len(records)}")

print(f"\nExtracted {len(records)} records from PDF")
print("Sample:")
for r in records[:5]:
    print(f"  {r['app_no']:15} | {r['name'][:45]:45} | {r['state']}")

# ── Match against institutions DB ─────────────────────────────────────────────
from app.core.database import SessionLocal
from app.models.institution import Institution
from sqlalchemy import select

db = SessionLocal()

# Build lookups
# 1. permanent_id → Institution
by_pid = {}
all_insts = db.execute(select(Institution)).scalars().all()
for inst in all_insts:
    if inst.permanent_id:
        by_pid[inst.permanent_id.strip()] = inst

# 2. normalized name → Institution (for fuzzy matching)
def normalize(s):
    return re.sub(r'[^A-Z0-9]', '', s.upper())

by_name = {}
for inst in all_insts:
    key = normalize(inst.name)
    if key not in by_name:
        by_name[key] = inst

print(f"\nInstitutions in DB: {len(all_insts)}")
print(f"By permanent_id: {len(by_pid)}")

matched_pid = 0
matched_name = 0
not_found = 0
updated = 0

for rec in records:
    inst = None

    # Try permanent_id match first
    if rec["app_no"] in by_pid:
        inst = by_pid[rec["app_no"]]
        matched_pid += 1

    # Try name match
    if not inst:
        key = normalize(rec["name"])
        if key in by_name:
            inst = by_name[key]
            matched_name += 1

    if inst:
        changed = False
        if rec["state"] and not inst.state:
            inst.state = rec["state"]
            changed = True
        if rec["address"] and not inst.address:
            inst.address = rec["address"][:500]
            changed = True
        if rec["website"] and not inst.website:
            w = rec["website"].strip()
            if not w.startswith("http"):
                w = "https://" + w
            inst.website = w
            changed = True
        if changed:
            updated += 1
    else:
        not_found += 1

db.commit()

# Final stats
from sqlalchemy import text
with_state = db.query(Institution).filter(Institution.state.isnot(None)).count()
tn_count   = db.query(Institution).filter(Institution.state == "Tamil Nadu").count()
rows = db.execute(
    text("SELECT state, COUNT(*) cnt FROM institutions WHERE state IS NOT NULL GROUP BY state ORDER BY cnt DESC LIMIT 30")
).fetchall()
db.close()

print(f"\nMatching results:")
print(f"  By permanent_id : {matched_pid}")
print(f"  By name         : {matched_name}")
print(f"  Not found       : {not_found}")
print(f"  Records updated : {updated}")
print(f"\nTotal with state: {with_state} / 4634")
print(f"Tamil Nadu count: {tn_count}")
print(f"\nTop states:")
for s, c in rows:
    print(f"  {s:<35} {c}")
