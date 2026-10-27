"""
Fetch state data via Wikipedia API — synchronous, reliable version.
Searches Wikipedia for each institution and extracts state from categories.
"""
import sys, re, time, requests
sys.path.insert(0, '.')

WIKI_API = "https://en.wikipedia.org/w/api.php"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "AICTE-Dashboard/1.0 (state data enrichment)"})

# All Indian states and key cities
STATE_WORDS = {
    # States (direct match in category)
    "karnataka": "Karnataka", "maharashtra": "Maharashtra",
    "tamil nadu": "Tamil Nadu", "telangana": "Telangana",
    "andhra pradesh": "Andhra Pradesh", "kerala": "Kerala",
    "uttar pradesh": "Uttar Pradesh", "rajasthan": "Rajasthan",
    "gujarat": "Gujarat", "madhya pradesh": "Madhya Pradesh",
    "west bengal": "West Bengal", "odisha": "Odisha",
    "bihar": "Bihar", "jharkhand": "Jharkhand",
    "punjab": "Punjab", "haryana": "Haryana",
    "delhi": "Delhi", "uttarakhand": "Uttarakhand",
    "himachal pradesh": "Himachal Pradesh",
    "jammu and kashmir": "Jammu & Kashmir",
    "jammu & kashmir": "Jammu & Kashmir",
    "assam": "Assam", "chhattisgarh": "Chhattisgarh",
    "goa": "Goa", "chandigarh": "Chandigarh",
    "puducherry": "Puducherry", "pondicherry": "Puducherry",
    "manipur": "Manipur", "meghalaya": "Meghalaya",
    "mizoram": "Mizoram", "nagaland": "Nagaland",
    "tripura": "Tripura", "sikkim": "Sikkim",
    "arunachal pradesh": "Arunachal Pradesh",
    # Major cities → state
    "bengaluru": "Karnataka", "bangalore": "Karnataka",
    "mysuru": "Karnataka", "mysore": "Karnataka",
    "mangaluru": "Karnataka", "hubballi": "Karnataka",
    "mumbai": "Maharashtra", "pune": "Maharashtra",
    "nagpur": "Maharashtra", "nashik": "Maharashtra",
    "aurangabad": "Maharashtra", "kolhapur": "Maharashtra",
    "hyderabad": "Telangana",
    "visakhapatnam": "Andhra Pradesh", "vijayawada": "Andhra Pradesh",
    "tirupati": "Andhra Pradesh",
    "chennai": "Tamil Nadu", "coimbatore": "Tamil Nadu",
    "madurai": "Tamil Nadu", "tiruchirappalli": "Tamil Nadu",
    "thiruvananthapuram": "Kerala", "kochi": "Kerala",
    "kozhikode": "Kerala", "thrissur": "Kerala",
    "kolkata": "West Bengal", "calcutta": "West Bengal",
    "ahmedabad": "Gujarat", "surat": "Gujarat",
    "vadodara": "Gujarat", "rajkot": "Gujarat",
    "jaipur": "Rajasthan", "jodhpur": "Rajasthan",
    "udaipur": "Rajasthan", "kota": "Rajasthan",
    "lucknow": "Uttar Pradesh", "kanpur": "Uttar Pradesh",
    "agra": "Uttar Pradesh", "varanasi": "Uttar Pradesh",
    "meerut": "Uttar Pradesh", "allahabad": "Uttar Pradesh",
    "ghaziabad": "Uttar Pradesh", "noida": "Uttar Pradesh",
    "indore": "Madhya Pradesh", "bhopal": "Madhya Pradesh",
    "jabalpur": "Madhya Pradesh", "gwalior": "Madhya Pradesh",
    "bhubaneswar": "Odisha", "cuttack": "Odisha",
    "rourkela": "Odisha",
    "patna": "Bihar", "gaya": "Bihar",
    "ranchi": "Jharkhand", "jamshedpur": "Jharkhand",
    "amritsar": "Punjab", "ludhiana": "Punjab",
    "jalandhar": "Punjab", "patiala": "Punjab",
    "chandigarh": "Chandigarh",
    "faridabad": "Haryana", "gurgaon": "Haryana",
    "rohtak": "Haryana", "ambala": "Haryana",
    "dehradun": "Uttarakhand", "haridwar": "Uttarakhand",
    "roorkee": "Uttarakhand", "nainital": "Uttarakhand",
    "shimla": "Himachal Pradesh",
    "srinagar": "Jammu & Kashmir", "jammu": "Jammu & Kashmir",
    "guwahati": "Assam", "dibrugarh": "Assam",
    "raipur": "Chhattisgarh", "bhilai": "Chhattisgarh",
    "panaji": "Goa",
}

def parse_state_from_categories(categories: list) -> str | None:
    """Extract state from Wikipedia category list."""
    for cat in categories:
        cl = cat.lower().replace("category:", "")
        for keyword, state in STATE_WORDS.items():
            if keyword in cl:
                return state
    return None

def get_state(name: str) -> str | None:
    try:
        # Search Wikipedia
        r = SESSION.get(WIKI_API, params={
            "action": "query", "list": "search",
            "srsearch": name + " India",
            "srlimit": 3, "format": "json",
        }, timeout=8)
        results = r.json().get("query", {}).get("search", [])
        if not results:
            return None

        # Get categories for best match
        r2 = SESSION.get(WIKI_API, params={
            "action": "query", "titles": results[0]["title"],
            "prop": "categories", "cllimit": 50, "format": "json",
        }, timeout=8)
        pages = r2.json().get("query", {}).get("pages", {})
        cats = []
        for page in pages.values():
            cats.extend(c["title"] for c in page.get("categories", []))
        return parse_state_from_categories(cats)
    except Exception:
        return None

# Quick validation
print("Validating:")
tests = [
    ("Bangalore Institute of Technology", "Karnataka"),
    ("Anna University", "Tamil Nadu"),
    ("Pune Institute of Technology", "Maharashtra"),
]
for name, expected in tests:
    got = get_state(name)
    print(f"  {'OK' if got == expected else 'FAIL'}: {name} -> {got} (expected {expected})")
print()

# ── Main enrichment ───────────────────────────────────────────────────────────
from app.core.database import SessionLocal
from app.models.institution import Institution
from sqlalchemy import select, text

db = SessionLocal()
insts = db.execute(
    select(Institution).where(Institution.state.is_(None))
).scalars().all()
total = len(insts)
db.close()
print(f"Processing {total} institutions...")

found = 0
for i, inst in enumerate(insts):
    state = get_state(inst.name)
    if state:
        db2 = SessionLocal()
        obj = db2.get(Institution, inst.id)
        if obj:
            obj.state = state
            db2.commit()
        db2.close()
        found += 1

    if (i + 1) % 50 == 0 or i == 0:
        hit = found / (i+1) * 100
        print(f"  [{i+1}/{total}] found={found} ({hit:.0f}%)", flush=True)

    time.sleep(0.3)  # ~3 req/sec, polite rate for Wikipedia

# Final stats
db = SessionLocal()
with_state = db.query(Institution).filter(Institution.state.isnot(None)).count()
rows = db.execute(
    text("SELECT state, COUNT(*) cnt FROM institutions WHERE state IS NOT NULL GROUP BY state ORDER BY cnt DESC LIMIT 25")
).fetchall()
db.close()

print(f"\nDone!")
print(f"  Found state: {found} new + existing = {with_state} / 4634 total")
print(f"\nTop states:")
for s, c in rows:
    print(f"  {s:<35} {c}")
