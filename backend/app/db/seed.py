"""
Seed script for the AICTE Complaint Dashboard.

DEMO DATA - Not actual AICTE records.

Creates:
  - 6 Bureaus, 5 Regions
  - 8 ComplaintCategories
  - 10 Institutions (fictional)
  - 8 Demo Users (password: Demo@1234)
  - 15 Complaints + 15 Cases
  - 3 Overlap scenarios + 1 false-positive
  - SLA rules, overlap alerts, notifications, action histories

Usage:
  python -m app.db.seed
  DATABASE_URL=sqlite:///./dev.db python -m app.db.seed
"""
from __future__ import annotations

import os
import sys
import uuid
import logging
from datetime import date, datetime, timedelta, timezone

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_seed(db_url: str) -> None:
    """Clear and repopulate the database with demo data."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    _is_sqlite = db_url.startswith("sqlite")
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False} if _is_sqlite else {},
        echo=False,
    )

    # Import models so metadata is populated
    from app.models.base import Base
    import app.models.bureau        # noqa: F401
    import app.models.user          # noqa: F401
    import app.models.institution   # noqa: F401
    import app.models.complaint     # noqa: F401
    import app.models.case          # noqa: F401
    import app.models.overlap       # noqa: F401
    import app.models.notification  # noqa: F401

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()

    try:
        _clear_tables(db)
        logger.info("Tables cleared.")

        bureaus = _seed_bureaus(db)
        regions = _seed_regions(db)
        categories = _seed_categories(db)
        institutions = _seed_institutions(db, regions)
        users = _seed_users(db, bureaus, regions)
        sla_rules = _seed_sla_rules(db, bureaus, categories)
        complaints, cases = _seed_complaints_and_cases(
            db, bureaus, institutions, categories, users
        )
        _seed_overlap_alerts(db, cases, institutions, users)
        _seed_notifications(db, cases, users)

        db.commit()
        logger.info("Seed completed successfully.")
    except Exception:
        db.rollback()
        logger.exception("Seed failed — rolled back.")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------

def _clear_tables(db) -> None:
    from app.models.overlap import OverlapAlert, OverlapReview
    from app.models.notification import Notification, SLARule
    from app.models.case import (
        Case, CaseAssignment, CaseAction, CaseDocument, RelatedCase
    )
    from app.models.complaint import Complaint, ComplaintDocument, ComplaintCategory
    from app.models.institution import Institution, InstitutionAlias
    from app.models.user import User
    from app.models.bureau import Bureau, Region

    for model in [
        OverlapReview, OverlapAlert, Notification, SLARule,
        CaseDocument, CaseAction, CaseAssignment, RelatedCase, Case,
        ComplaintDocument, Complaint, ComplaintCategory,
        InstitutionAlias, Institution,
        User, Bureau, Region,
    ]:
        db.query(model).delete(synchronize_session=False)
    db.flush()


# ---------------------------------------------------------------------------
# Bureaus
# ---------------------------------------------------------------------------

def _seed_bureaus(db) -> dict:
    from app.models.bureau import Bureau
    data = [
        ("RB",   "Regulation Bureau",                 "Handles regulatory compliance of institutions"),
        ("PGRC", "Public Grievance Redressal Cell",   "Processes public grievances against institutions"),
        ("AB",   "Approval Bureau",                    "Manages institution approval and affiliation"),
        ("EB",   "Examination Bureau",                 "Oversees examination-related matters"),
        ("QB",   "Quality Bureau",                     "Monitors academic quality and accreditation"),
        ("IT",   "IT Cell",                            "Information Technology and portal management"),
    ]
    bureaus: dict[str, Bureau] = {}
    for code, name, desc in data:
        b = Bureau(code=code, name=name, description=desc)
        db.add(b)
        bureaus[code] = b
    db.flush()
    logger.info("Seeded %d bureaus.", len(bureaus))
    return bureaus


# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------

def _seed_regions(db) -> dict:
    from app.models.bureau import Region
    data = [
        ("NORTH",   "Northern Region",  ["Delhi", "Haryana", "Punjab", "Himachal Pradesh", "Uttarakhand", "J&K"]),
        ("SOUTH",   "Southern Region",  ["Tamil Nadu", "Kerala", "Karnataka", "Andhra Pradesh", "Telangana"]),
        ("EAST",    "Eastern Region",   ["West Bengal", "Odisha", "Bihar", "Jharkhand", "Assam"]),
        ("WEST",    "Western Region",   ["Maharashtra", "Gujarat", "Rajasthan", "Goa"]),
        ("CENTRAL", "Central Region",   ["Madhya Pradesh", "Chhattisgarh", "Uttar Pradesh"]),
    ]
    regions: dict[str, Region] = {}
    for code, name, states in data:
        r = Region(code=code, name=name, states=states)
        db.add(r)
        regions[code] = r
    db.flush()
    logger.info("Seeded %d regions.", len(regions))
    return regions


# ---------------------------------------------------------------------------
# Complaint categories
# ---------------------------------------------------------------------------

def _seed_categories(db) -> dict:
    from app.models.complaint import ComplaintCategory
    data = [
        ("fee_refund",              "Fee Refund",                 "Complaints regarding fee refund",             30),
        ("unapproved_program",      "Unapproved Program",         "Running unapproved courses/programs",         21),
        ("academic_malpractice",    "Academic Malpractice",       "Malpractice in academics / examinations",     14),
        ("faculty_shortage",        "Faculty Shortage",           "Insufficient or unqualified faculty",         30),
        ("infrastructure_deficiency","Infrastructure Deficiency", "Inadequate physical infrastructure",          30),
        ("affiliation_violation",   "Affiliation Violation",      "Violation of affiliation norms",              21),
        ("exam_irregularity",       "Exam Irregularity",          "Irregularities in conduct of examinations",   14),
        ("other",                   "Other",                      "Miscellaneous complaints",                    30),
    ]
    cats: dict[str, ComplaintCategory] = {}
    for code, name, desc, sla in data:
        c = ComplaintCategory(code=code, name=name, description=desc, default_sla_days=sla)
        db.add(c)
        cats[code] = c
    db.flush()
    logger.info("Seeded %d categories.", len(cats))
    return cats


# ---------------------------------------------------------------------------
# Institutions
# ---------------------------------------------------------------------------

def _seed_institutions(db, regions: dict) -> dict:
    from app.models.institution import Institution, InstitutionAlias, InstitutionType, AliasType

    data = [
        {
            "key": "ETU",
            "permanent_id": "1-1234567",
            "name": "Excellent Technical University",
            "city": "Pune", "state": "Maharashtra",
            "region": "WEST",
            "type": InstitutionType.engineering,
            "aliases": ["ETU Pune", "Excellent Tech Univ"],
        },
        {
            "key": "PMC",
            "permanent_id": "1-2345678",
            "name": "Progressive Management College",
            "city": "Delhi", "state": "Delhi",
            "region": "NORTH",
            "type": InstitutionType.management,
            "aliases": ["Progressive Management Col", "PMC Delhi"],
        },
        {
            "key": "FPI",
            "permanent_id": "1-3456789",
            "name": "Future Pharmacy Institute",
            "city": "Hyderabad", "state": "Telangana",
            "region": "SOUTH",
            "type": InstitutionType.pharmacy,
            "aliases": ["Future Pharmcy Institute", "FPI Hyderabad"],
        },
        {
            "key": "MEC",
            "permanent_id": "1-4567890",
            "name": "Metro Engineering College",
            "city": "Mumbai", "state": "Maharashtra",
            "region": "WEST",
            "type": InstitutionType.engineering,
            "aliases": ["Metro Engg College"],
        },
        {
            "key": "PP",
            "permanent_id": "1-5678901",
            "name": "Pioneer Polytechnic",
            "city": "Chennai", "state": "Tamil Nadu",
            "region": "SOUTH",
            "type": InstitutionType.polytechnic,
            "aliases": ["Pioneer Polytec"],
        },
        {
            "key": "NAS",
            "permanent_id": "1-6789012",
            "name": "National Architecture School",
            "city": "Bangalore", "state": "Karnataka",
            "region": "SOUTH",
            "type": InstitutionType.architecture,
            "aliases": [],
        },
        {
            "key": "SBS",
            "permanent_id": "1-7890123",
            "name": "Sunrise Business School",
            "city": "Kolkata", "state": "West Bengal",
            "region": "EAST",
            "type": InstitutionType.management,
            "aliases": [],
        },
        {
            "key": "TVI",
            "permanent_id": "1-8901234",
            "name": "Tech Valley Institute",
            "city": "Ahmedabad", "state": "Gujarat",
            "region": "WEST",
            "type": InstitutionType.engineering,
            "aliases": [],
        },
        {
            "key": "GVPC",
            "permanent_id": "1-9012345",
            "name": "Green Valley Pharmacy College",
            "city": "Jaipur", "state": "Rajasthan",
            "region": "WEST",
            "type": InstitutionType.pharmacy,
            "aliases": [],
        },
        {
            "key": "NSE",
            "permanent_id": "1-0123456",
            "name": "North Star Engineering",
            "city": "Lucknow", "state": "Uttar Pradesh",
            "region": "CENTRAL",
            "type": InstitutionType.engineering,
            "aliases": [],
        },
    ]

    institutions: dict[str, Institution] = {}
    for d in data:
        inst = Institution(
            permanent_id=d["permanent_id"],
            name=d["name"],
            city=d["city"],
            state=d["state"],
            region_id=regions[d["region"]].id,
            institution_type=d["type"],
            is_active=True,
        )
        db.add(inst)
        db.flush()
        for alias_name in d["aliases"]:
            db.add(InstitutionAlias(
                institution_id=inst.id,
                alias=alias_name,
                alias_type=AliasType.abbreviation,
            ))
        institutions[d["key"]] = inst

    db.flush()
    logger.info("Seeded %d institutions.", len(institutions))
    return institutions


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def _seed_users(db, bureaus: dict, regions: dict) -> dict:
    from app.models.user import User, UserRole
    from app.core.security import hash_password

    pwd = hash_password("Demo@1234")
    data = [
        {
            "key": "admin",
            "email": "admin@aicte.gov.in",
            "full_name": "System Administrator",
            "role": UserRole.system_admin,
            "bureau": None, "region": None,
            "is_superuser": True,
            "employee_id": "AICTE-ADM-001",
        },
        {
            "key": "rb_officer",
            "email": "rb.officer@aicte.gov.in",
            "full_name": "RB Officer (Demo)",
            "role": UserRole.rb_officer,
            "bureau": "RB", "region": None,
            "is_superuser": False,
            "employee_id": "AICTE-RB-001",
        },
        {
            "key": "pgrc_officer",
            "email": "pgrc.officer@aicte.gov.in",
            "full_name": "PGRC Officer (Demo)",
            "role": UserRole.pgrc_officer,
            "bureau": "PGRC", "region": None,
            "is_superuser": False,
            "employee_id": "AICTE-PGRC-001",
        },
        {
            "key": "pgrc_officer2",
            "email": "pgrc.officer2@aicte.gov.in",
            "full_name": "PGRC Officer 2 (Demo)",
            "role": UserRole.pgrc_officer,
            "bureau": "PGRC", "region": None,
            "is_superuser": False,
            "employee_id": "AICTE-PGRC-002",
        },
        {
            "key": "ab_officer",
            "email": "ab.officer@aicte.gov.in",
            "full_name": "AB Officer (Demo)",
            "role": UserRole.bureau_officer,
            "bureau": "AB", "region": None,
            "is_superuser": False,
            "employee_id": "AICTE-AB-001",
        },
        {
            "key": "north_regional",
            "email": "north.regional@aicte.gov.in",
            "full_name": "North Regional Officer (Demo)",
            "role": UserRole.regional_officer,
            "bureau": None, "region": "NORTH",
            "is_superuser": False,
            "employee_id": "AICTE-REG-NORTH-001",
        },
        {
            "key": "south_regional",
            "email": "south.regional@aicte.gov.in",
            "full_name": "South Regional Officer (Demo)",
            "role": UserRole.regional_officer,
            "bureau": None, "region": "SOUTH",
            "is_superuser": False,
            "employee_id": "AICTE-REG-SOUTH-001",
        },
        {
            "key": "management",
            "email": "management@aicte.gov.in",
            "full_name": "Senior Management (Demo)",
            "role": UserRole.senior_management,
            "bureau": None, "region": None,
            "is_superuser": False,
            "employee_id": "AICTE-MGMT-001",
        },
    ]

    users: dict[str, User] = {}
    for d in data:
        u = User(
            email=d["email"],
            hashed_password=pwd,
            full_name=d["full_name"],
            role=d["role"],
            bureau_id=bureaus[d["bureau"]].id if d["bureau"] else None,
            region_id=regions[d["region"]].id if d["region"] else None,
            is_active=True,
            is_superuser=d["is_superuser"],
            employee_id=d["employee_id"],
        )
        db.add(u)
        users[d["key"]] = u

    db.flush()
    logger.info("Seeded %d users.", len(users))
    return users


# ---------------------------------------------------------------------------
# SLA rules
# ---------------------------------------------------------------------------

def _seed_sla_rules(db, bureaus: dict, categories: dict) -> list:
    from app.models.notification import SLARule

    rules_data = [
        # Global defaults
        {"bureau": None, "category": None, "priority": "normal",   "sla_days": 30, "warning_days": 5},
        {"bureau": None, "category": None, "priority": "high",     "sla_days": 15, "warning_days": 3},
        {"bureau": None, "category": None, "priority": "critical", "sla_days": 7,  "warning_days": 2},
        # Per-bureau
        {"bureau": "RB",   "category": None, "priority": None, "sla_days": 21, "warning_days": 4},
        {"bureau": "PGRC", "category": None, "priority": None, "sla_days": 30, "warning_days": 5},
        {"bureau": "AB",   "category": None, "priority": None, "sla_days": 45, "warning_days": 7},
        # Category-specific
        {"bureau": None, "category": "fee_refund",        "priority": None, "sla_days": 30, "warning_days": 5},
        {"bureau": None, "category": "academic_malpractice", "priority": None, "sla_days": 14, "warning_days": 3},
        {"bureau": None, "category": "exam_irregularity", "priority": None, "sla_days": 14, "warning_days": 3},
    ]

    rules = []
    for d in rules_data:
        r = SLARule(
            bureau_id=bureaus[d["bureau"]].id if d["bureau"] else None,
            category_id=categories[d["category"]].id if d["category"] else None,
            priority=d["priority"],
            sla_days=d["sla_days"],
            warning_days=d["warning_days"],
            escalation_days=2,
            is_active=True,
        )
        db.add(r)
        rules.append(r)

    db.flush()
    logger.info("Seeded %d SLA rules.", len(rules))
    return rules


# ---------------------------------------------------------------------------
# Complaints and Cases
# ---------------------------------------------------------------------------

def _seed_complaints_and_cases(
    db, bureaus: dict, institutions: dict, categories: dict, users: dict
) -> tuple[list, list]:
    from app.models.complaint import Complaint, ComplaintSource, ComplaintStatus, ComplaintPriority
    from app.models.case import Case, CaseStatus, CasePriority, CaseAction, CaseActionType, CaseAssignment

    today = date.today()
    admin = users["admin"]
    rb = users["rb_officer"]
    pgrc = users["pgrc_officer"]
    pgrc2 = users["pgrc_officer2"]
    ab = users["ab_officer"]

    def _dt(days_ago: int) -> datetime:
        return datetime.now(timezone.utc) - timedelta(days=days_ago)

    def _d(days_ago: int) -> date:
        return today - timedelta(days=days_ago)

    # complaint_number, case_number, bureau_key, institution_key, category_key,
    # subject, description, status, priority, received_days_ago, sla_days,
    # expected_disposal_offset (relative to created), disposal_done
    complaint_specs = [
        # ── Scenario 1: Institution ETU has RB + PGRC cases (overlap) ──
        {
            "cn": "COMP-2024-001", "case_num": "CASE-2024-001",
            "bureau": "RB", "institution": "ETU", "category": "affiliation_violation",
            "subject": "Affiliation violation - running unapproved engineering branch",
            "description": (
                "Excellent Technical University, Pune has been found running "
                "a new engineering branch (Artificial Intelligence) without AICTE approval. "
                "Students have been admitted without disclosing this fact."
            ),
            "status": CaseStatus.under_process, "priority": CasePriority.high,
            "received": 45, "sla": 15, "disposal_offset": 15, "disposed": False,
            "assignee": "rb_officer",
        },
        {
            "cn": "COMP-2024-002", "case_num": "CASE-2024-002",
            "bureau": "PGRC", "institution": "ETU", "category": "fee_refund",
            "subject": "Fee refund not processed - Excellent Technical University",
            "description": (
                "Student from Excellent Technical University, Pune complains that "
                "fee refund for cancelled admission has not been processed for over 3 months. "
                "Amount: Rs. 1,20,000/-. Multiple follow-ups have been ignored."
            ),
            "status": CaseStatus.pending_assignment, "priority": CasePriority.normal,
            "received": 20, "sla": 30, "disposal_offset": 30, "disposed": False,
            "assignee": "pgrc_officer",
        },
        # ── Scenario 2: PMC name variant (overlap via fuzzy name) ──
        {
            "cn": "COMP-2024-003", "case_num": "CASE-2024-003",
            "bureau": "PGRC", "institution": "PMC", "category": "fee_refund",
            "subject": "Unpaid fee refund - Progressive Management College Delhi",
            "description": (
                "Student from Progressive Management College, Delhi has not received "
                "the fee refund of Rs. 85,000 after cancelling admission. "
                "Complaint filed with institution was unanswered."
            ),
            "status": CaseStatus.under_process, "priority": CasePriority.normal,
            "received": 30, "sla": 30, "disposal_offset": 30, "disposed": False,
            "assignee": "pgrc_officer",
        },
        {
            # Same institution but slightly different name in raw field
            "cn": "COMP-2024-004", "case_num": "CASE-2024-004",
            "bureau": "AB", "institution": "PMC", "category": "unapproved_program",
            "subject": "Unapproved MBA program - Progressive Management Col Delhi",
            "description": (
                "Progressive Management Col (Delhi) is offering an MBA program "
                "without valid AICTE approval. Students enrolled are unaware. "
                "This is a duplicate complaint from a different student."
            ),
            "status": CaseStatus.received, "priority": CasePriority.high,
            "received": 10, "sla": 21, "disposal_offset": 21, "disposed": False,
            "assignee": "ab_officer",
            "institution_name_raw": "Progressive Management Col",
        },
        # ── Scenario 3: FPI fee-refund from 2 students to different bureaus ──
        {
            "cn": "COMP-2024-005", "case_num": "CASE-2024-005",
            "bureau": "PGRC", "institution": "FPI", "category": "fee_refund",
            "subject": "Fee refund pending - Future Pharmacy Institute Hyderabad",
            "description": (
                "Student A from Future Pharmacy Institute, Hyderabad reports that "
                "admission fee of Rs. 60,000 was not refunded after programme cancellation. "
                "Written complaint to institution on 15-Sep-2024 was ignored."
            ),
            "status": CaseStatus.under_process, "priority": CasePriority.normal,
            "received": 8, "sla": 30, "disposal_offset": 30, "disposed": False,
            "assignee": "pgrc_officer2",
        },
        {
            "cn": "COMP-2024-006", "case_num": "CASE-2024-006",
            "bureau": "RB", "institution": "FPI", "category": "fee_refund",
            "subject": "Refund not provided by Future Pharmacy Institute",
            "description": (
                "Student B from Future Pharmacy Institute, Hyderabad also reports "
                "non-refund of admission fee of Rs. 60,000. Same issue as another complaint. "
                "Pattern of non-refund suggested. Complaint filed within same week."
            ),
            "status": CaseStatus.received, "priority": CasePriority.normal,
            "received": 5, "sla": 30, "disposal_offset": 30, "disposed": False,
            "assignee": "rb_officer",
        },
        # ── False positive: NSE and ETU both are engineering colleges but different ──
        {
            "cn": "COMP-2024-007", "case_num": "CASE-2024-007",
            "bureau": "RB", "institution": "NSE", "category": "faculty_shortage",
            "subject": "Severe faculty shortage at North Star Engineering",
            "description": (
                "North Star Engineering, Lucknow has severe shortage of qualified faculty. "
                "Only 5 out of required 30 positions are filled. "
                "Students are suffering from inadequate instruction."
            ),
            "status": CaseStatus.under_process, "priority": CasePriority.high,
            "received": 25, "sla": 15, "disposal_offset": 15, "disposed": False,
            "assignee": "rb_officer",
        },
        {
            "cn": "COMP-2024-008", "case_num": "CASE-2024-008",
            "bureau": "RB", "institution": "TVI", "category": "faculty_shortage",
            "subject": "Faculty shortage at Tech Valley Institute",
            "description": (
                "Tech Valley Institute, Ahmedabad has insufficient qualified faculty "
                "in the computer science department. 8 out of 20 positions are vacant. "
                "Academic calendar is affected."
            ),
            "status": CaseStatus.under_process, "priority": CasePriority.normal,
            "received": 18, "sla": 30, "disposal_offset": 30, "disposed": False,
            "assignee": "rb_officer",
        },
        # ── Overdue cases ──
        {
            "cn": "COMP-2024-009", "case_num": "CASE-2024-009",
            "bureau": "PGRC", "institution": "MEC", "category": "infrastructure_deficiency",
            "subject": "Infrastructure deficiency at Metro Engineering College",
            "description": (
                "Metro Engineering College, Mumbai has inadequate laboratory facilities. "
                "Computer labs are outdated with non-functional equipment. "
                "Students are unable to complete practical coursework."
            ),
            "status": CaseStatus.awaiting_information, "priority": CasePriority.normal,
            "received": 65, "sla": 30, "disposal_offset": -35, "disposed": False,
            "assignee": "pgrc_officer",
        },
        {
            "cn": "COMP-2024-010", "case_num": "CASE-2024-010",
            "bureau": "AB", "institution": "PP", "category": "affiliation_violation",
            "subject": "Affiliation norm violation - Pioneer Polytechnic",
            "description": (
                "Pioneer Polytechnic, Chennai is admitting students beyond its sanctioned intake. "
                "Approved intake is 120 but 189 students were admitted this year. "
                "Affiliation conditions are being violated."
            ),
            "status": CaseStatus.under_process, "priority": CasePriority.high,
            "received": 50, "sla": 15, "disposal_offset": -35, "disposed": False,
            "assignee": "ab_officer",
        },
        {
            "cn": "COMP-2024-011", "case_num": "CASE-2024-011",
            "bureau": "EB", "institution": "NAS", "category": "exam_irregularity",
            "subject": "Mass copying in end-semester exam - National Architecture School",
            "description": (
                "Reports of organized cheating during end-semester examinations at "
                "National Architecture School, Bangalore. Invigilators appear to have "
                "facilitated the malpractice."
            ),
            "status": CaseStatus.escalated, "priority": CasePriority.critical,
            "received": 40, "sla": 7, "disposal_offset": -33, "disposed": False,
            "assignee": "rb_officer",
        },
        # ── Disposed cases ──
        {
            "cn": "COMP-2024-012", "case_num": "CASE-2024-012",
            "bureau": "PGRC", "institution": "SBS", "category": "fee_refund",
            "subject": "Fee refund resolved - Sunrise Business School",
            "description": "Student fee refund issue at Sunrise Business School Kolkata.",
            "status": CaseStatus.disposed, "priority": CasePriority.normal,
            "received": 90, "sla": 30, "disposal_offset": 28,
            "disposed": True,
            "disposal_remarks": "Institution has refunded Rs. 75,000 to student. Case disposed.",
            "assignee": "pgrc_officer",
        },
        {
            "cn": "COMP-2024-013", "case_num": "CASE-2024-013",
            "bureau": "RB", "institution": "GVPC", "category": "unapproved_program",
            "subject": "Unapproved B.Pharm program - Green Valley Pharmacy College",
            "description": "Green Valley Pharmacy College Jaipur running unapproved B.Pharm specialization.",
            "status": CaseStatus.closed, "priority": CasePriority.normal,
            "received": 120, "sla": 21, "disposal_offset": 20,
            "disposed": True,
            "disposal_remarks": "Programme discontinued. Warning issued. Case closed.",
            "assignee": "rb_officer",
        },
        {
            "cn": "COMP-2024-014", "case_num": "CASE-2024-014",
            "bureau": "QB", "institution": "ETU", "category": "academic_malpractice",
            "subject": "Academic malpractice in research publications - ETU",
            "description": (
                "Faculty members at Excellent Technical University Pune were found to "
                "have plagiarised research papers. University failed to investigate "
                "internal complaints."
            ),
            "status": CaseStatus.disposed, "priority": CasePriority.high,
            "received": 75, "sla": 14, "disposal_offset": 13,
            "disposed": True,
            "disposal_remarks": "Show-cause notice issued. Faculty penalised. Case disposed.",
            "assignee": "rb_officer",
        },
        {
            "cn": "COMP-2024-015", "case_num": "CASE-2024-015",
            "bureau": "PGRC", "institution": "MEC", "category": "other",
            "subject": "Hostel fee overcharge - Metro Engineering College",
            "description": "Metro Engineering College Mumbai overcharging hostel fees beyond approved rates.",
            "status": CaseStatus.disposed, "priority": CasePriority.normal,
            "received": 100, "sla": 30, "disposal_offset": 27,
            "disposed": True,
            "disposal_remarks": "College directed to refund excess fees. Compliance verified. Case disposed.",
            "assignee": "pgrc_officer2",
        },
    ]

    complaints_list = []
    cases_list = []

    for spec in complaint_specs:
        received_date = _d(spec["received"])
        comp = Complaint(
            complaint_number=spec["cn"],
            institution_id=institutions[spec["institution"]].id,
            institution_name_raw=spec.get("institution_name_raw", institutions[spec["institution"]].name),
            source=ComplaintSource.portal,
            category_id=categories[spec["category"]].id,
            subject=spec["subject"],
            description=spec["description"],
            received_date=received_date,
            complainant_name="Demo Complainant (DEMO DATA)",
            is_anonymous=False,
            bureau_id=bureaus[spec["bureau"]].id,
            status=ComplaintStatus(spec["status"].value),
            priority=ComplaintPriority(spec["priority"].value),
            created_by_id=admin.id,
        )
        comp.created_at = _dt(spec["received"])
        db.add(comp)
        db.flush()

        # Created date
        created_dt = _dt(spec["received"])
        disposal_date = None
        disposal_remarks = None
        expected_disposal = _d(spec["received"]) + timedelta(days=spec["sla"])
        # Negative disposal_offset means it's already past
        if spec.get("disposed"):
            disposal_date = _d(spec["received"]) + timedelta(days=abs(spec["disposal_offset"]))
            disposal_remarks = spec.get("disposal_remarks")

        c = Case(
            case_number=spec["case_num"],
            complaint_id=comp.id,
            institution_id=institutions[spec["institution"]].id,
            bureau_id=bureaus[spec["bureau"]].id,
            category_id=categories[spec["category"]].id,
            subject=spec["subject"],
            description=spec["description"],
            status=spec["status"],
            priority=spec["priority"],
            sla_days=spec["sla"],
            expected_disposal_date=expected_disposal,
            disposal_date=disposal_date,
            disposal_remarks=disposal_remarks,
            created_by_id=admin.id,
        )
        c.created_at = created_dt
        c.updated_at = created_dt
        db.add(c)
        db.flush()

        # Assignment
        assignee = users[spec["assignee"]]
        assignment = CaseAssignment(
            case_id=c.id,
            assigned_to_id=assignee.id,
            assigned_by_id=admin.id,
            is_current=True,
        )
        db.add(assignment)

        # Action history for a few cases
        if spec["case_num"] in ("CASE-2024-001", "CASE-2024-009", "CASE-2024-012"):
            action = CaseAction(
                case_id=c.id,
                action_type=CaseActionType.status_change,
                description=f"Case status updated to {spec['status'].value}. (DEMO DATA)",
                performed_by_id=assignee.id,
                old_status="received",
                new_status=spec["status"].value,
            )
            db.add(action)

        complaints_list.append(comp)
        cases_list.append(c)

    db.flush()
    logger.info("Seeded %d complaints and %d cases.", len(complaints_list), len(cases_list))
    return complaints_list, cases_list


# ---------------------------------------------------------------------------
# Overlap alerts
# ---------------------------------------------------------------------------

def _seed_overlap_alerts(db, cases: list, institutions: dict, users: dict) -> None:
    from app.models.overlap import OverlapAlert, OverlapAlertStatus, MatchType

    def _case_by_num(num: str):
        for c in cases:
            if c.case_number == num:
                return c
        raise ValueError(f"Case {num} not found")

    alert_specs = [
        # Scenario 1: ETU - RB case vs PGRC case (same institution, different issues)
        {
            "num": "OA-2024-001",
            "incoming": "CASE-2024-001",
            "existing": "CASE-2024-002",
            "institution": "ETU",
            "match_type": MatchType.exact_id,
            "score": 95.0,
            "status": OverlapAlertStatus.pending_review,
            "evidence": {
                "matched_by": ["exact_id"],
                "scores": {"institution": 100.0, "text": 42.0, "combined": 95.0},
                "note": "Same institution (permanent_id 1-1234567). Different complaint types.",
            },
        },
        # Scenario 2: PMC name variant
        {
            "num": "OA-2024-002",
            "incoming": "CASE-2024-003",
            "existing": "CASE-2024-004",
            "institution": "PMC",
            "match_type": MatchType.institution_name_fuzzy,
            "score": 88.0,
            "status": OverlapAlertStatus.pending_review,
            "evidence": {
                "matched_by": ["institution_name_fuzzy"],
                "scores": {"institution": 92.0, "text": 71.0, "combined": 88.0},
                "note": "Fuzzy name match: 'Progressive Management College' vs 'Progressive Management Col'",
            },
        },
        # Scenario 3: FPI fee-refund from 2 students
        {
            "num": "OA-2024-003",
            "incoming": "CASE-2024-005",
            "existing": "CASE-2024-006",
            "institution": "FPI",
            "match_type": MatchType.combined,
            "score": 91.0,
            "status": OverlapAlertStatus.pending_review,
            "evidence": {
                "matched_by": ["exact_id", "complaint_text"],
                "scores": {"institution": 100.0, "text": 78.0, "combined": 91.0},
                "note": "Same institution + similar fee-refund complaints filed within 1 week",
            },
        },
        # False positive: NSE (engineering) vs TVI (engineering) - similar issue, different institution
        {
            "num": "OA-2024-004",
            "incoming": "CASE-2024-007",
            "existing": "CASE-2024-008",
            "institution": None,  # different institutions
            "match_type": MatchType.complaint_similarity,
            "score": 72.0,
            "status": OverlapAlertStatus.false_positive,  # already marked false positive
            "evidence": {
                "matched_by": ["complaint_text"],
                "scores": {"institution": 0.0, "text": 72.0, "combined": 72.0},
                "note": "Similar faculty-shortage text but different institutions. Marked false positive.",
            },
        },
    ]

    for spec in alert_specs:
        c_incoming = _case_by_num(spec["incoming"])
        c_existing = _case_by_num(spec["existing"])

        bureaus_involved = []
        if c_incoming.bureau_id:
            bureaus_involved.append(str(c_incoming.bureau_id))
        if c_existing.bureau_id:
            b2 = str(c_existing.bureau_id)
            if b2 not in bureaus_involved:
                bureaus_involved.append(b2)

        alert = OverlapAlert(
            alert_number=spec["num"],
            case_id_incoming=c_incoming.id,
            case_id_existing=c_existing.id,
            institution_id=institutions[spec["institution"]].id if spec["institution"] else None,
            match_type=spec["match_type"],
            match_score=spec["score"],
            match_evidence=spec["evidence"],
            bureaus_involved=bureaus_involved,
            status=spec["status"],
        )
        db.add(alert)

    db.flush()
    logger.info("Seeded 4 overlap alerts (3 real + 1 false positive).")


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def _seed_notifications(db, cases: list, users: dict) -> None:
    from app.models.notification import Notification, NotificationType

    admin = users["admin"]
    rb = users["rb_officer"]
    pgrc = users["pgrc_officer"]

    def _case_by_num(num: str):
        for c in cases:
            if c.case_number == num:
                return c
        return None

    notif_data = [
        {
            "user": "admin",
            "title": "Welcome to AICTE Complaint Dashboard",
            "message": "DEMO DATA - This is a demo environment. Password: Demo@1234 for all users.",
            "type": NotificationType.system,
            "entity_type": None, "entity_id": None,
        },
        {
            "user": "admin",
            "title": "3 Overlap Alerts Pending Review",
            "message": "There are 3 pending overlap alerts that require your review. (DEMO DATA)",
            "type": NotificationType.overlap_alert,
            "entity_type": "overlap_alert", "entity_id": None,
        },
        {
            "user": "rb_officer",
            "title": "Case Assigned to You",
            "message": "Case CASE-2024-001 (ETU affiliation violation) has been assigned to you. (DEMO DATA)",
            "type": NotificationType.assignment,
            "entity_type": "case", "entity_id": _case_by_num("CASE-2024-001"),
        },
        {
            "user": "pgrc_officer",
            "title": "Deadline Approaching",
            "message": "Case CASE-2024-009 is overdue. Expected disposal was 35 days ago. (DEMO DATA)",
            "type": NotificationType.overdue,
            "entity_type": "case", "entity_id": _case_by_num("CASE-2024-009"),
        },
        {
            "user": "pgrc_officer",
            "title": "Overlap Alert Detected",
            "message": "Overlap alert OA-2024-003 detected for FPI fee-refund cases. (DEMO DATA)",
            "type": NotificationType.overlap_alert,
            "entity_type": "overlap_alert", "entity_id": None,
        },
    ]

    for d in notif_data:
        entity_id = None
        if d["entity_id"] and hasattr(d["entity_id"], "id"):
            entity_id = d["entity_id"].id

        n = Notification(
            user_id=users[d["user"]].id,
            title=d["title"],
            message=d["message"],
            notification_type=d["type"],
            related_entity_type=d["entity_type"],
            related_entity_id=entity_id,
            is_read=False,
        )
        db.add(n)

    db.flush()
    logger.info("Seeded demo notifications.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _db_url = os.getenv(
        "DATABASE_URL",
        "sqlite:///./aicte_dev.db",
    )
    logger.info("Running seed with DATABASE_URL=%s", _db_url)
    run_seed(_db_url)
    logger.info("Done.")
