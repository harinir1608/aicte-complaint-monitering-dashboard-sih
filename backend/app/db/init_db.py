"""
Database initialization helpers.

Called at startup (or manually) to seed essential reference data:
  - Default complaint categories
  - Default bureaus and regions
"""
from __future__ import annotations

import logging
from sqlalchemy.orm import Session
from sqlalchemy import select

logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """Idempotently create default reference data.

    Safe to call multiple times — skips records that already exist.
    """
    _create_default_categories(db)
    _create_default_bureaus(db)
    _create_default_regions(db)
    db.commit()
    logger.info("init_db completed.")


def _create_default_categories(db: Session) -> None:
    from app.models.complaint import ComplaintCategory

    existing_count = db.execute(
        select(ComplaintCategory)
    ).scalars().first()
    if existing_count is not None:
        return  # Categories already seeded

    default_categories = [
        {"code": "FEE", "name": "Fee Related", "description": "Grievances related to fee collection", "default_sla_days": 30},
        {"code": "FACULTY", "name": "Faculty Related", "description": "Complaints about faculty conduct or shortage", "default_sla_days": 45},
        {"code": "INFRA", "name": "Infrastructure", "description": "Campus infrastructure and facilities", "default_sla_days": 60},
        {"code": "AFFIL", "name": "Affiliation", "description": "Affiliation and recognition issues", "default_sla_days": 90},
        {"code": "ADMIT", "name": "Admission", "description": "Admission process and eligibility", "default_sla_days": 30},
        {"code": "EXAM", "name": "Examination", "description": "Examination irregularities and results", "default_sla_days": 30},
        {"code": "MGMT", "name": "Management Issues", "description": "Governance and management disputes", "default_sla_days": 45},
        {"code": "OTHER", "name": "Other", "description": "Miscellaneous complaints", "default_sla_days": 30},
    ]

    for cat_data in default_categories:
        cat = ComplaintCategory(**cat_data)
        db.add(cat)

    logger.info("Created %d default complaint categories.", len(default_categories))


def _create_default_bureaus(db: Session) -> None:
    from app.models.bureau import Bureau

    existing = db.execute(select(Bureau)).scalars().first()
    if existing is not None:
        return  # Bureaus already seeded

    default_bureaus = [
        {"code": "RB", "name": "Regional Bureau", "description": "Handles regional institution complaints", "is_active": True},
        {"code": "PGRC", "name": "Post Graduate Redressal Cell", "description": "Handles PG student grievances", "is_active": True},
        {"code": "AB", "name": "Approval Bureau", "description": "Handles institution approval complaints", "is_active": True},
        {"code": "FNB", "name": "Finance & Accounts Bureau", "description": "Handles financial grievances", "is_active": True},
    ]

    for bureau_data in default_bureaus:
        bureau = Bureau(**bureau_data)
        db.add(bureau)

    logger.info("Created %d default bureaus.", len(default_bureaus))


def _create_default_regions(db: Session) -> None:
    from app.models.bureau import Region

    existing = db.execute(select(Region)).scalars().first()
    if existing is not None:
        return  # Regions already seeded

    default_regions = [
        {
            "code": "NORTH",
            "name": "Northern Region",
            "description": "Delhi, UP, Punjab, Haryana, HP, J&K, Uttarakhand, Rajasthan",
            "states": ["Delhi", "Uttar Pradesh", "Punjab", "Haryana", "Himachal Pradesh", "Jammu & Kashmir", "Uttarakhand", "Rajasthan"],
            "is_active": True,
        },
        {
            "code": "SOUTH",
            "name": "Southern Region",
            "description": "Tamil Nadu, Karnataka, Kerala, Andhra Pradesh, Telangana",
            "states": ["Tamil Nadu", "Karnataka", "Kerala", "Andhra Pradesh", "Telangana"],
            "is_active": True,
        },
        {
            "code": "EAST",
            "name": "Eastern Region",
            "description": "West Bengal, Odisha, Bihar, Jharkhand, NE states",
            "states": ["West Bengal", "Odisha", "Bihar", "Jharkhand", "Assam", "Meghalaya", "Manipur", "Nagaland", "Mizoram", "Tripura", "Arunachal Pradesh", "Sikkim"],
            "is_active": True,
        },
        {
            "code": "WEST",
            "name": "Western Region",
            "description": "Maharashtra, Gujarat, Goa, Madhya Pradesh, Chhattisgarh",
            "states": ["Maharashtra", "Gujarat", "Goa", "Madhya Pradesh", "Chhattisgarh"],
            "is_active": True,
        },
        {
            "code": "CENTRAL",
            "name": "Central Region",
            "description": "Madhya Pradesh, Chhattisgarh, UP (partial)",
            "states": ["Madhya Pradesh", "Chhattisgarh"],
            "is_active": True,
        },
    ]

    for region_data in default_regions:
        region = Region(**region_data)
        db.add(region)

    logger.info("Created %d default regions.", len(default_regions))
