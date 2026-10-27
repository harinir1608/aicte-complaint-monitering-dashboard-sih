"""
Extract state directly from institution names using:
1. State names embedded in name (e.g. "RAJASTHAN TECHNICAL UNIVERSITY")
2. University affiliations (e.g. "ANNA UNIVERSITY" → Tamil Nadu)
3. Known university suffixes and abbreviations
"""
import sys, re
sys.path.insert(0, '.')

# Direct state names that appear in institution names
STATE_NAMES_IN_NAME = {
    "RAJASTHAN": "Rajasthan",
    "GUJARAT": "Gujarat",
    "KARNATAKA": "Karnataka",
    "KERALA": "Kerala",
    "ANDHRA": "Andhra Pradesh",
    "TELANGANA": "Telangana",
    "MAHARASHTRA": "Maharashtra",
    "PUNJAB": "Punjab",
    "HARYANA": "Haryana",
    "ODISHA": "Odisha",
    "ORISSA": "Odisha",
    "ASSAM": "Assam",
    "TRIPURA": "Tripura",
    "MANIPUR": "Manipur",
    "MEGHALAYA": "Meghalaya",
    "MIZORAM": "Mizoram",
    "NAGALAND": "Nagaland",
    "CHHATTISGARH": "Chhattisgarh",
    "UTTARAKHAND": "Uttarakhand",
    "UTTARANCHAL": "Uttarakhand",
    "JHARKHAND": "Jharkhand",
    "GOA": "Goa",
    "SIKKIM": "Sikkim",
    "CHANDIGARH": "Chandigarh",
    "PONDICHERRY": "Puducherry",
    "PUDUCHERRY": "Puducherry",
}

# Well-known universities/institutes → state
KNOWN_INSTITUTIONS = {
    "ANNA UNIVERSITY": "Tamil Nadu",
    "VTU": "Karnataka", "VISVESVARAYA": "Karnataka",
    "OSMANIA": "Telangana", "KAKATIYA": "Telangana",
    "JNTUH": "Telangana", "JNTUK": "Andhra Pradesh", "JNTUA": "Andhra Pradesh",
    "ANDHRA UNIVERSITY": "Andhra Pradesh",
    "CALICUT UNIVERSITY": "Kerala", "KERALA UNIVERSITY": "Kerala",
    "MG UNIVERSITY": "Kerala", "APJ ABDUL KALAM TECHNICAL UNIVERSITY": "Uttar Pradesh",
    "AKTU": "Uttar Pradesh", "UPTU": "Uttar Pradesh",
    "MDU": "Haryana", "MAHARSHI DAYANAND": "Haryana",
    "PANJAB UNIVERSITY": "Punjab", "PUNJABI UNIVERSITY": "Punjab",
    "SPPU": "Maharashtra", "SAVITRIBAI PHULE PUNE": "Maharashtra",
    "MUMBAI UNIVERSITY": "Maharashtra", "NAGPUR UNIVERSITY": "Maharashtra",
    "RTM NAGPUR": "Maharashtra", "SWAMI RAMANAND TEERTH": "Maharashtra",
    "RGPV": "Madhya Pradesh", "DAVV": "Madhya Pradesh",
    "DEVI AHILYA": "Madhya Pradesh",
    "RAJIV GANDHI PRODYUOGIKI": "Madhya Pradesh",
    "BHOPAL": "Madhya Pradesh",
    "RAJASTHAN TECHNICAL": "Rajasthan",
    "JNV UNIVERSITY": "Rajasthan", "JNVU": "Rajasthan",
    "KUK": "Haryana", "KURUKSHETRA": "Haryana",
    "CRSU": "Haryana",
    "HPTU": "Himachal Pradesh",
    "JKBOSE": "Jammu & Kashmir",
    "CALCUTTA UNIVERSITY": "West Bengal", "BURDWAN UNIVERSITY": "West Bengal",
    "JADAVPUR": "West Bengal", "KALYANI UNIVERSITY": "West Bengal",
    "NORTH BENGAL": "West Bengal",
    "PATNA UNIVERSITY": "Bihar", "MAGADH UNIVERSITY": "Bihar",
    "RANCHI UNIVERSITY": "Jharkhand", "VINOBA BHAVE": "Jharkhand",
    "BPUT": "Odisha", "BHUBANESWAR": "Odisha",
    "UTKAL UNIVERSITY": "Odisha",
    "VBSPU": "Uttar Pradesh", "GGSIPU": "Delhi",
    "GURU GOBIND SINGH INDRAPRASTHA": "Delhi",
    "MDU ROHTAK": "Haryana",
    "THAPAR": "Punjab",
    "AMRITSAR": "Punjab",
    "GULBARGA UNIVERSITY": "Karnataka",
    "MYSORE UNIVERSITY": "Karnataka",
    "TUMKUR UNIVERSITY": "Karnataka",
    "KANNUR UNIVERSITY": "Kerala", "MAHATMA GANDHI UNIVERSITY": "Kerala",
    "KOTTAYAM": "Kerala",
    "BHARATHIDASAN": "Tamil Nadu", "BHARATHIAR": "Tamil Nadu",
    "MADURAI KAMARAJ": "Tamil Nadu", "ALAGAPPA": "Tamil Nadu",
    "MANONMANIAM SUNDARANAR": "Tamil Nadu",
    "PONDICHERRY UNIVERSITY": "Puducherry",
    "GUJARAT UNIVERSITY": "Gujarat", "GTU": "Gujarat",
    "VEER NARMAD SOUTH GUJARAT": "Gujarat", "SAURASHTRA": "Gujarat",
    "HEMCHANDRACHARYA NORTH GUJARAT": "Gujarat",
    "NIRMA UNIVERSITY": "Gujarat",
    "DBATU": "Maharashtra", "DR BABASAHEB AMBEDKAR TECHNOLOGICAL": "Maharashtra",
    "SOLAPUR UNIVERSITY": "Maharashtra",
    "SHIVAJI UNIVERSITY": "Maharashtra",
    "NORTH MAHARASHTRA": "Maharashtra",
    "DR BHIM RAO AMBEDKAR": "Uttar Pradesh",
    "BUNDELKHAND UNIVERSITY": "Uttar Pradesh",
    "DR RAM MANOHAR LOHIA": "Uttar Pradesh",
    "MJP ROHILKHAND": "Uttar Pradesh",
    "LUCKNOW UNIVERSITY": "Uttar Pradesh",
    "CHHATRAPATI SHAHU JI MAHARAJ": "Uttar Pradesh",
    "GAUR": "Uttar Pradesh",
    "IKG PTU": "Punjab", "IKGPTU": "Punjab",
    "MRSPTU": "Punjab",
}

def infer_state_from_name(name: str) -> str | None:
    upper = name.upper()

    # Check known institutions first (more specific)
    for kw, state in KNOWN_INSTITUTIONS.items():
        if kw.upper() in upper:
            return state

    # Check for state names directly in the institution name
    for state_kw, state in STATE_NAMES_IN_NAME.items():
        # Use word boundary-like check
        pattern = r'\b' + re.escape(state_kw) + r'\b'
        if re.search(pattern, upper):
            # Avoid false positives: "ANDHRA" should match "ANDHRA PRADESH" context
            return state

    return None

# ── Run ───────────────────────────────────────────────────────────────────────
from app.core.database import SessionLocal
from app.models.institution import Institution
from sqlalchemy import select, text

db = SessionLocal()
insts = db.execute(
    select(Institution).where(Institution.state.is_(None))
).scalars().all()
print(f"Processing {len(insts)} institutions without state...")

updated = 0
for inst in insts:
    state = infer_state_from_name(inst.name)
    if state:
        inst.state = state
        updated += 1

db.commit()
with_state = db.query(Institution).filter(Institution.state.isnot(None)).count()
rows = db.execute(
    text("SELECT state, COUNT(*) cnt FROM institutions WHERE state IS NOT NULL GROUP BY state ORDER BY cnt DESC LIMIT 25")
).fetchall()
db.close()

print(f"\nUpdated: {updated}")
print(f"Total with state: {with_state} / 4634")
print(f"\nTop states:")
for s, c in rows:
    print(f"  {s:<35} {c}")
