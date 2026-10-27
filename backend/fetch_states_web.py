"""
Fetch state information for AICTE institutions using web search.
Uses DuckDuckGo HTML search + BeautifulSoup to extract state names.
Processes in concurrent batches of 10 with rate limiting.
"""
import sys, re, time, asyncio, json
sys.path.insert(0, '.')

import httpx
from bs4 import BeautifulSoup

# Indian states list for extraction
STATES = [
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
    "Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka",
    "Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram",
    "Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu",
    "Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal",
    "Delhi","Jammu & Kashmir","Ladakh","Chandigarh","Puducherry",
    "Andaman and Nicobar","Lakshadweep","Dadra and Nagar Haveli","Daman and Diu",
    # Common abbreviations
    "J&K","J & K","U.P.","M.P.","T.N.",
]
# Sorted longest first
STATES_SORTED = sorted(STATES, key=len, reverse=True)
STATE_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(s) for s in STATES_SORTED) + r')\b',
    re.IGNORECASE
)
# Normalize abbreviations
NORMALIZE = {
    "U.P.": "Uttar Pradesh", "M.P.": "Madhya Pradesh", "T.N.": "Tamil Nadu",
    "J&K": "Jammu & Kashmir", "J & K": "Jammu & Kashmir",
    "Andaman and Nicobar": "Andaman & Nicobar Islands",
    "Dadra and Nagar Haveli": "Dadra & Nagar Haveli",
    "Daman and Diu": "Daman & Diu",
}

def extract_state_from_text(text: str) -> str | None:
    m = STATE_PATTERN.search(text)
    if m:
        s = m.group(1)
        return NORMALIZE.get(s, s)
    return None

# ── DuckDuckGo search ─────────────────────────────────────────────────────────
DDG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

async def search_ddg(client: httpx.AsyncClient, name: str) -> str | None:
    """Search DuckDuckGo for institution state."""
    query = f"{name} india college location state"
    try:
        r = await client.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query, "kl": "in-en"},
            headers=DDG_HEADERS,
            timeout=10.0,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "lxml")
        # Extract all visible text from results
        texts = []
        for result in soup.select(".result__snippet, .result__title, .result__url"):
            texts.append(result.get_text(" ", strip=True))
        full = " ".join(texts)
        return extract_state_from_text(full)
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
    print(f"Processing {total} institutions without state...")
    db.close()

    found = 0
    errors = 0
    processed = 0
    BATCH = 8
    DELAY = 1.2  # seconds between batches

    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
    async with httpx.AsyncClient(limits=limits) as client:
        for i in range(0, total, BATCH):
            batch = insts[i:i+BATCH]
            tasks = [search_ddg(client, inst.name) for inst in batch]
            results = await asyncio.gather(*tasks)

            db = SessionLocal()
            for inst, state in zip(batch, results):
                processed += 1
                if state:
                    inst_fresh = db.get(Institution, inst.id)
                    if inst_fresh:
                        inst_fresh.state = state
                    found += 1
            db.commit()
            db.close()

            pct = (processed / total) * 100
            print(f"  [{processed}/{total}] {pct:.1f}% — found: {found}", flush=True)

            # Rate limit
            await asyncio.sleep(DELAY)

    # Final stats
    db = SessionLocal()
    from sqlalchemy import text
    with_state = db.query(Institution).filter(Institution.state.isnot(None)).count()
    top = db.execute(
        text("SELECT state, COUNT(*) cnt FROM institutions WHERE state IS NOT NULL GROUP BY state ORDER BY cnt DESC LIMIT 20")
    ).fetchall()
    db.close()

    print(f"\n{'='*50}")
    print(f"Done!")
    print(f"  Found state for: {found} / {total}")
    print(f"  Total with state: {with_state} / 4634")
    print(f"\nTop states:")
    for s, c in top:
        print(f"  {s:<35} {c}")

asyncio.run(main())
