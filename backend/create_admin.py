"""Quick script to create an admin user for testing."""
import sys, os
sys.path.insert(0, '.')

from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.user import User
from app.models.bureau import Bureau, Region
from app.core.security import hash_password

# Create all tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Create bureaus if they don't exist
bureaus = [
    Bureau(code="RB", name="Regulation Bureau", description="Handles regulatory matters", is_active=True),
    Bureau(code="PGRC", name="Public Grievance Redressal Cell", description="Handles public grievances", is_active=True),
    Bureau(code="AB", name="Approval Bureau", description="Handles approvals", is_active=True),
]
for b in bureaus:
    existing = db.query(Bureau).filter_by(code=b.code).first()
    if not existing:
        db.add(b)

# Create regions
regions = [
    Region(code="NR", name="Northern Region", description="Northern states", states=["UP","UK","HP","Punjab","Haryana","Delhi","J&K"], is_active=True),
    Region(code="SR", name="Southern Region", description="Southern states", states=["TN","AP","Telangana","Karnataka","Kerala"], is_active=True),
    Region(code="WR", name="Western Region", description="Western states", states=["Maharashtra","Gujarat","Goa","Rajasthan"], is_active=True),
    Region(code="ER", name="Eastern Region", description="Eastern states", states=["WB","Odisha","Bihar","Jharkhand"], is_active=True),
    Region(code="CR", name="Central Region", description="Central states", states=["MP","CG"], is_active=True),
]
for r in regions:
    existing = db.query(Region).filter_by(code=r.code).first()
    if not existing:
        db.add(r)

db.commit()

# Create admin user
existing = db.query(User).filter_by(email="admin@aicte.gov.in").first()
if not existing:
    admin = User(
        email="admin@aicte.gov.in",
        hashed_password=hash_password("Admin@1234"),
        full_name="System Administrator",
        employee_id="AICTE-ADMIN-001",
        role="system_admin",
        is_active=True,
        is_superuser=True,
    )
    db.add(admin)
    db.commit()
    print("✅ Admin user created: admin@aicte.gov.in / Admin@1234")
else:
    print("✅ Admin user already exists: admin@aicte.gov.in / Admin@1234")

# Create RB officer
existing = db.query(User).filter_by(email="rb.officer@aicte.gov.in").first()
if not existing:
    rb_bureau = db.query(Bureau).filter_by(code="RB").first()
    rb = User(
        email="rb.officer@aicte.gov.in",
        hashed_password=hash_password("Demo@1234"),
        full_name="RB Officer Demo",
        employee_id="AICTE-RB-001",
        role="rb_officer",
        bureau_id=rb_bureau.id if rb_bureau else None,
        is_active=True,
    )
    db.add(rb)
    db.commit()
    print("✅ RB Officer created: rb.officer@aicte.gov.in / Demo@1234")

# Create PGRC officer
existing = db.query(User).filter_by(email="pgrc.officer@aicte.gov.in").first()
if not existing:
    pgrc_bureau = db.query(Bureau).filter_by(code="PGRC").first()
    pgrc = User(
        email="pgrc.officer@aicte.gov.in",
        hashed_password=hash_password("Demo@1234"),
        full_name="PGRC Officer Demo",
        employee_id="AICTE-PGRC-001",
        role="pgrc_officer",
        bureau_id=pgrc_bureau.id if pgrc_bureau else None,
        is_active=True,
    )
    db.add(pgrc)
    db.commit()
    print("✅ PGRC Officer created: pgrc.officer@aicte.gov.in / Demo@1234")

db.close()
print("\n📋 Demo accounts:")
print("  admin@aicte.gov.in     / Admin@1234  (System Admin)")
print("  rb.officer@aicte.gov.in / Demo@1234  (RB Officer)")
print("  pgrc.officer@aicte.gov.in / Demo@1234 (PGRC Officer)")
