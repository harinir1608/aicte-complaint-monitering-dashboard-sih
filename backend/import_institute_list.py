"""
Extract ALL institution state/district/city data from Institute_List (1).pdf
Columns: Institute Permanent ID | Institute Name | State | District | City
Match to institutions table by permanent_id (primary) or name (fallback)
"""
import sys, re
sys.path.insert(0, '.')

import pdfplumber

PDF_PATH = "C:/Users/meena/Desktop/ps22/data/Institute_List (1).pdf"

def clean(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', str(text).replace('\n', ' ').strip())

print("Extracting records from PDF (794 pages)...")
records = []

with pdfplumber.open(PDF_PATH) as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                if not row or len(row) < 3:
                    continue
                pid   = clean(row[0])
                name  = clean(row[1])
                state = clean(row[2])
                dist  = clean(row[3]) if len(row) > 3 else ""
                city  = clean(row[4]) if len(row) > 4 else ""

                # Skip header rows
                if "permanent" in pid.lower() or "institute" in pid.lower():
                    continue
                # Skip empty
                if not pid and not name:
                    continue
                if not state or state.lower() in ("state", ""):
                    continue

                records.append({
                    "pid":      pid.strip(),
                    "name":     name.strip(),
                    "state":    state.strip(),
                    "district": dist.strip(),
                    "city":     city.strip(),
                })

        if (i + 1) % 100 == 0:
            print(f"  Page {i+1}/794 — {len(records)} records so far")

print(f"\nExtracted {len(records)} total records")
print("Sample records:")
for r in records[:5]:
    print(f"  PID={r['pid']:15} | {r['name'][:40]:40} | {r['state']} | {r['district']} | {r['city']}")

# ── Deduplicate (keep first occurrence per pid) ───────────────────────────────
seen = set()
unique = []
for r in records:
    key = r["pid"] if r["pid"] else r["name"].upper()
    if key and key not in seen:
        seen.add(key)
        unique.append(r)

print(f"Unique records: {len(unique)}")

# ── Match to institutions DB ──────────────────────────────────────────────────
from app.core.database import SessionLocal
from app.models.institution import Institution
from sqlalchemy import select

db = SessionLocal()
all_insts = db.execute(select(Institution)).scalars().all()

# Build lookup by permanent_id
by_pid = {}
for inst in all_insts:
    if inst.permanent_id:
        by_pid[inst.permanent_id.strip()] = inst

# Build lookup by normalized name
def norm(s):
    return re.sub(r'[^A-Z0-9]', '', s.upper())

by_name = {}
for inst in all_insts:
    key = norm(inst.name)
    if key not in by_name:
        by_name[key] = inst

print(f"\nDB institutions: {len(all_insts)}")

matched_pid = 0
matched_name = 0
not_found = 0
updated_state = 0
updated_district = 0
updated_city = 0

for rec in unique:
    inst = by_pid.get(rec["pid"]) if rec["pid"] else None

    if not inst and rec["name"]:
        inst = by_name.get(norm(rec["name"]))
        if inst:
            matched_name += 1
    elif inst:
        matched_pid += 1

    if not inst:
        not_found += 1
        continue

    changed = False
    if rec["state"] and not inst.state:
        inst.state = rec["state"]
        updated_state += 1
        changed = True
    if rec["district"] and not inst.district:
        inst.district = rec["district"].title()
        updated_district += 1
        changed = True
    if rec["city"] and not inst.city:
        inst.city = rec["city"].title()
        updated_city += 1
        changed = True

db.commit()

# ── Final stats ───────────────────────────────────────────────────────────────
from sqlalchemy import text
with_state    = db.query(Institution).filter(Institution.state.isnot(None)).count()
with_district = db.query(Institution).filter(Institution.district.isnot(None)).count()
with_city     = db.query(Institution).filter(Institution.city.isnot(None)).count()

rows = db.execute(
    text("SELECT state, COUNT(*) cnt FROM institutions WHERE state IS NOT NULL GROUP BY state ORDER BY cnt DESC")
).fetchall()
db.close()

print(f"\n{'='*60}")
print(f"Results:")
print(f"  Matched by permanent_id : {matched_pid}")
print(f"  Matched by name         : {matched_name}")
print(f"  Not found in DB         : {not_found}")
print(f"  States updated          : {updated_state}")
print(f"  Districts updated       : {updated_district}")
print(f"  Cities updated          : {updated_city}")
print(f"\nDB coverage after update:")
print(f"  With state    : {with_state} / 4634")
print(f"  With district : {with_district} / 4634")
print(f"  With city     : {with_city} / 4634")
print(f"\nAll states:")
for s, c in rows:
    print(f"  {s:<35} {c}")
