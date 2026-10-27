"""
Migrate all 4788 institutions from the Neon PostgreSQL temp table
into the AICTE dashboard's SQLite institutions table.
"""
import sys, os, uuid
sys.path.insert(0, '.')

# ── Connect to Neon (source) ──────────────────────────────────────────────────
import psycopg2

NEON_URL = "postgresql://neondb_owner:npg_X49KDLyTsJVW@ep-divine-paper-axyquc4b-pooler.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require"

print("Connecting to Neon PostgreSQL...")
neon_conn = psycopg2.connect(NEON_URL)
neon_cur = neon_conn.cursor()
neon_cur.execute("SELECT sno, application_no, permanent_id, institute_name FROM temp ORDER BY sno")
rows = neon_cur.fetchall()
neon_conn.close()
print(f"Fetched {len(rows)} records from Neon temp table")

# ── Connect to AICTE SQLite (destination) ─────────────────────────────────────
from app.core.database import SessionLocal
from app.models.institution import Institution
from app.models.user import User
from sqlalchemy import text
from datetime import datetime, timezone

db = SessionLocal()

# Get the admin user id to set as created_by
admin = db.query(User).filter_by(email="admin@aicte.gov.in").first()
admin_id = admin.id if admin else None

# Get existing permanent_ids to avoid duplicates
existing_pids = set(
    r[0] for r in db.execute(text("SELECT permanent_id FROM institutions WHERE permanent_id IS NOT NULL")).fetchall()
)
existing_names = set(
    r[0].upper() for r in db.execute(text("SELECT name FROM institutions")).fetchall()
)
print(f"Existing institutions: {db.query(Institution).count()} (will skip duplicates)")

# ── Map application_no prefix to institution_type ─────────────────────────────
def guess_type(name: str) -> str:
    n = name.upper()
    if any(k in n for k in ["PHARMACY", "PHARMA", "PHARM"]):
        return "pharmacy"
    if any(k in n for k in ["POLYTECHNIC", "POLY", "DIPLOMA"]):
        return "polytechnic"
    if any(k in n for k in ["ARCHITECT"]):
        return "architecture"
    if any(k in n for k in ["MANAGEMENT", "BUSINESS", "MBA", "MCA", "COMMERCE"]):
        return "management"
    if any(k in n for k in ["ENGINEERING", "ENGG", "TECH", "COLLEGE OF"]):
        return "engineering"
    return "other"

# ── Batch insert ──────────────────────────────────────────────────────────────
now = datetime.now(timezone.utc)
inserted = 0
skipped_dup = 0
BATCH = 200

new_institutions = []
for sno, app_no, permanent_id, name in rows:
    # Skip if permanent_id already exists
    if permanent_id and permanent_id.strip() in existing_pids:
        skipped_dup += 1
        continue
    # Skip if name already exists (case-insensitive)
    if name.upper() in existing_names:
        skipped_dup += 1
        continue

    inst = Institution(
        id=uuid.uuid4(),
        permanent_id=permanent_id.strip() if permanent_id and permanent_id.strip() else None,
        name=name.strip(),
        institution_type=guess_type(name),
        is_active=True,
        created_at=now,
        updated_at=now,
        created_by_id=admin_id,
    )
    new_institutions.append(inst)
    if permanent_id and permanent_id.strip():
        existing_pids.add(permanent_id.strip())
    existing_names.add(name.upper())

    # Commit in batches
    if len(new_institutions) >= BATCH:
        db.bulk_save_objects(new_institutions)
        db.commit()
        inserted += len(new_institutions)
        new_institutions = []
        print(f"  Inserted {inserted} so far...")

# Final batch
if new_institutions:
    db.bulk_save_objects(new_institutions)
    db.commit()
    inserted += len(new_institutions)

total = db.query(Institution).count()
db.close()

print(f"\nDone!")
print(f"  Inserted : {inserted}")
print(f"  Skipped  : {skipped_dup} (duplicates)")
print(f"  Total in DB: {total}")
