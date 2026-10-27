"""
Fetch state data for AICTE institutions using Wikipedia's free API.
- Searches Wikipedia for each institution name
- Extracts state from page categories (e.g. "Engineering colleges in Karnataka")
- Processes concurrently with rate limiting
"""
import sys, re, asyncio, time
sys.path.insert(0, '.')

import httpx

# State extraction from Wikipedia category strings
STATE_PATTERN = re.compile(
    r'\bin\s+(Andhra Pradesh|Arunachal Pradesh|Assam|Bihar|Chhattisgarh|'
    r'Goa|Gujarat|Haryana|Himachal Pradesh|Jharkhand|Karnataka|Kerala|'
    r'Madhya Pradesh|Maharashtra|Manipur|Meghalaya|Mizoram|Nagaland|Odisha|'
    r'Punjab|Rajasthan|Sikkim|Tamil Nadu|Telangana|Tripura|Uttar Pradesh|'
    r'Uttarakhand|West Bengal|Delhi|Jammu and Kashmir|Jammu & Kashmir|'
    r'Chandigarh|Puducherry|Bengaluru|Bangalore|Mumbai|Kolkata|Hyderabad|'
    r'Chennai|Pune|Coimbatore|Jaipur|Lucknow|Nagpur|Ahmedabad|Surat|'
    r'Visakhapatnam|Kanpur|Indore|Bhopal|Patna|Ludhiana|Agra|Nashik)\b',
    re.IGNORECASE
)

# City-to-state for Wikipedia category city names
CITY_TO_STATE = {
    "bengaluru": "Karnataka", "bangalore": "Karnataka",
    "mumbai": "Maharashtra", "pune": "Maharashtra", "nagpur": "Maharashtra",
    "nashik": "Maharashtra",
    "kolkata": "West Bengal",
    "hyderabad": "Telangana",
    "chennai": "Tamil Nadu", "coimbatore": "Tamil Nadu",
    "ahmedabad": "Gujarat", "surat": "Gujarat",
    "jaipur": "Rajasthan",
    "lucknow": "Uttar Pradesh", "kanpur": "Uttar Pradesh", "agra": "Uttar Pradesh",
    "indore": "Madhya Pradesh", "bhopal": "Madhya Pradesh",
    "patna": "Bihar",
    "ludhiana": "Punjab",
    "visakhapatnam": "Andhra Pradesh",
}

STATE_MAP = {
    "jammu and kashmir": "Jammu & Kashmir",
    "jammu & kashmir": "Jammu & Kashmir",
}

def extract_state_from_categories(categories: list[str]) -> str | None:
    for cat in categories:
        cat_lower = cat.lower()
        m = STATE_PATTERN.search(cat)
        if m:
            word = m.group(1).lower()
            # Check if it's a city
            if word in CITY_TO_STATE:
                return CITY_TO_STATE[word]
            # Return as state (normalize)
            state = m.group(1)
            return STATE_MAP.get(state.lower(), state)
    return None

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "AICTE-Dashboard-StateEnricher/1.0 (educational data enrichment)"}

async def get_state_for_institution(client: httpx.AsyncClient, name: str) -> str | None:
    """Search Wikipedia and extract state from page categories."""
    try:
        # Step 1: Search for the institution
        r = await client.get(WIKI_API, params={
            "action": "query",
            "list": "search",
            "srsearch": f"{name} India",
            "srlimit": 3,
            "format": "json",
        }, headers=HEADERS, timeout=8.0)
        if r.status_code != 200:
            return None
        results = r.json().get("query", {}).get("search", [])
        if not results:
            return None

        # Step 2: Get categories for top result
        page_title = results[0]["title"]
        r2 = await client.get(WIKI_API, params={
            "action": "query",
            "titles": page_title,
            "prop": "categories",
            "cllimit": 50,
            "format": "json",
        }, headers=HEADERS, timeout=8.0)
        if r2.status_code != 200:
            return None
        pages = r2.json().get("query", {}).get("pages", {})
        cats = []
        for page in pages.values():
            cats.extend(c["title"] for c in page.get("categories", []))

        return extract_state_from_categories(cats)
    except Exception:
        return None

# ── Main ──────────────────────────────────────────────────────────────────────
from app.core.database import SessionLocal
from app.models.institution import Institution
from sqlalchemy import select

async def main():
    db = SessionLocal()
    insts = db.execute(
        select(Institution).where(Institution.state.is_(None))
    ).scalars().all()
    total = len(insts)
    print(f"Processing {total} institutions via Wikipedia API...")
    print("(Estimated time: ~{:.0f} min at 10 req/batch)".format(total * 1.5 / 60))
    db.close()

    found = 0
    processed = 0
    BATCH = 10
    DELAY = 1.0  # Wikipedia rate limit: be polite

    limits = httpx.Limits(max_connections=15, max_keepalive_connections=10)
    async with httpx.AsyncClient(limits=limits, http2=True) as client:
        for i in range(0, total, BATCH):
            batch = insts[i:i+BATCH]
            tasks = [get_state_for_institution(client, inst.name) for inst in batch]
            results = await asyncio.gather(*tasks)

            db = SessionLocal()
            for inst, state in zip(batch, results):
                processed += 1
                if state:
                    obj = db.get(Institution, inst.id)
                    if obj:
                        obj.state = state
                    found += 1
            db.commit()
            db.close()

            if processed % 100 == 0 or processed <= BATCH:
                pct = (processed / total) * 100
                hit_rate = (found / processed * 100) if processed else 0
                print(f"  [{processed}/{total}] {pct:.1f}% — found: {found} ({hit_rate:.0f}% hit rate)", flush=True)

            await asyncio.sleep(DELAY)

    # Final stats
    db = SessionLocal()
    from sqlalchemy import text
    with_state = db.query(Institution).filter(Institution.state.isnot(None)).count()
    top = db.execute(
        text("SELECT state, COUNT(*) cnt FROM institutions WHERE state IS NOT NULL GROUP BY state ORDER BY cnt DESC LIMIT 25")
    ).fetchall()
    db.close()

    print(f"\n{'='*55}")
    print(f"Wikipedia enrichment complete!")
    print(f"  Found state for : {found} / {total} institutions")
    print(f"  Total with state: {with_state} / 4634")
    print(f"\nTop states:")
    for s, c in top:
        print(f"  {s:<35} {c}")

asyncio.run(main())
