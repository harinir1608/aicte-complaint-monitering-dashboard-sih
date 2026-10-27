"""
Additional state enrichment:
1. State abbreviations in names (A.P., M.P., T.N., U.P., etc.)
2. City names after commas: "COLLEGE, PUNE" → Maharashtra
3. Hundreds more smaller towns/districts
"""
import sys, re
sys.path.insert(0, '.')

# State abbreviations
ABBREVIATIONS = {
    r'\bA\.P\.\b': "Andhra Pradesh",
    r'\bT\.N\.\b': "Tamil Nadu",
    r'\bM\.P\.\b': "Madhya Pradesh",
    r'\bU\.P\.\b': "Uttar Pradesh",
    r'\bH\.P\.\b': "Himachal Pradesh",
    r'\bW\.B\.\b': "West Bengal",
    r'\bJ\.K\.\b': "Jammu & Kashmir",
    r'\bJ\&K\b': "Jammu & Kashmir",
}

# Extended city → state (smaller towns and districts)
MORE_CITIES = {
    # Andhra Pradesh
    "TENALI": "Andhra Pradesh", "BAPATLA": "Andhra Pradesh",
    "ONGOLE": "Andhra Pradesh", "NANDYAL": "Andhra Pradesh",
    "KURNOOL": "Andhra Pradesh", "HINDUPUR": "Andhra Pradesh",
    "ANANTAPUR": "Andhra Pradesh", "KADAPA": "Andhra Pradesh",
    "CHITTOOR": "Andhra Pradesh", "TIRUPATI": "Andhra Pradesh",
    "GUNTUR": "Andhra Pradesh", "VIJAYAWADA": "Andhra Pradesh",
    "ELURU": "Andhra Pradesh", "BHIMAVARAM": "Andhra Pradesh",
    "RAJAHMUNDRY": "Andhra Pradesh", "KAKINADA": "Andhra Pradesh",
    "VIZIANAGARAM": "Andhra Pradesh", "SRIKAKULAM": "Andhra Pradesh",
    "AMALAPURAM": "Andhra Pradesh", "NARASARAOPETA": "Andhra Pradesh",
    "PRODDATUR": "Andhra Pradesh", "PONNUR": "Andhra Pradesh",
    "GUDUR": "Andhra Pradesh",
    # Maharashtra (more towns)
    "WANI": "Maharashtra", "NANDURBAR": "Maharashtra",
    "PETH VADGAON": "Maharashtra", "PETH": "Maharashtra",
    "CHOPDA": "Maharashtra", "MALKAPUR": "Maharashtra",
    "HINGOLI": "Maharashtra", "PARBHANI": "Maharashtra",
    "NANTEJ": "Maharashtra", "MURBAD": "Maharashtra",
    "SINNAR": "Maharashtra", "BARAMATI": "Maharashtra",
    "BARSHI": "Maharashtra", "AKLUJ": "Maharashtra",
    "SAWARDE": "Maharashtra", "MANDANGAD": "Maharashtra",
    "GEORAI": "Maharashtra", "GEORI TANDA": "Maharashtra",
    "KHARGHAR": "Maharashtra", "NAVI MUMBAI": "Maharashtra",
    "NAVIMUMBAI": "Maharashtra", "VASARNI": "Maharashtra",
    "PRAVARANAGAR": "Maharashtra", "BABHULGAON": "Maharashtra",
    "NARAYANGAON": "Maharashtra", "MANCHAR": "Maharashtra",
    "LATUR": "Maharashtra", "UDGIR": "Maharashtra",
    "AUSA": "Maharashtra",
    # Karnataka (more towns)
    "TUMKUR": "Karnataka", "BIDAR": "Karnataka",
    "RAICHUR": "Karnataka", "KOPPAL": "Karnataka",
    "GADAG": "Karnataka", "HASSAN": "Karnataka",
    "CHIKMAGALUR": "Karnataka", "KODAGU": "Karnataka",
    "HANAGAL": "Karnataka", "HALIYAL": "Karnataka",
    "RANEBENNUR": "Karnataka", "MUDHOL": "Karnataka",
    "SINDHANUR": "Karnataka", "YELAHANKA": "Karnataka",
    "DODDABALLAPUR": "Karnataka", "TUMKUR": "Karnataka",
    "KOLAR": "Karnataka", "CHINTAMANI": "Karnataka",
    # Tamil Nadu (more towns)
    "KARAIKUDI": "Tamil Nadu", "DEVAKOTTAI": "Tamil Nadu",
    "KOVILPATTI": "Tamil Nadu", "TIRUNELVELI": "Tamil Nadu",
    "PALAYAMKOTTAI": "Tamil Nadu", "RAJAPALAYAM": "Tamil Nadu",
    "TIRUPUR": "Tamil Nadu", "TIRUPPUR": "Tamil Nadu",
    "OOTY": "Tamil Nadu", "NILGIRIS": "Tamil Nadu",
    "YERCAUD": "Tamil Nadu", "HOSUR": "Tamil Nadu",
    "RANIPET": "Tamil Nadu", "VELLORE": "Tamil Nadu",
    "AMBATTUR": "Tamil Nadu", "AVADI": "Tamil Nadu",
    "KANCHEEPURAM": "Tamil Nadu", "CHENGALPATTU": "Tamil Nadu",
    "VILLUPURAM": "Tamil Nadu", "CUDDALORE": "Tamil Nadu",
    "THIRUVARUR": "Tamil Nadu", "THANJAVUR": "Tamil Nadu",
    "MAYILADUTHURAI": "Tamil Nadu", "KARUR": "Tamil Nadu",
    "NAMAKKAL": "Tamil Nadu", "ERODE": "Tamil Nadu",
    "TIRUCHENGODE": "Tamil Nadu", "PERUNDURAI": "Tamil Nadu",
    "BHAVANI": "Tamil Nadu", "GOBICHETTIPALAYAM": "Tamil Nadu",
    "SATHYAMANGALAM": "Tamil Nadu", "ANTHIYUR": "Tamil Nadu",
    "AVANASHI": "Tamil Nadu", "METTUPALAYAM": "Tamil Nadu",
    "POLLACHI": "Tamil Nadu", "VALPARAI": "Tamil Nadu",
    "PALANI": "Tamil Nadu", "UDUMALPET": "Tamil Nadu",
    "ODDANCHATRAM": "Tamil Nadu", "DINDIGUL": "Tamil Nadu",
    "VEDASANDUR": "Tamil Nadu",
    # Kerala (more towns)
    "THIRUVALLA": "Kerala", "MANNANAM": "Kerala",
    "KOTTARAKKARA": "Kerala", "MAVELIKKARA": "Kerala",
    "CHENGANNUR": "Kerala", "PATHANAMTHITTA": "Kerala",
    "PUNALUR": "Kerala", "KAYAMKULAM": "Kerala",
    "HARIPAD": "Kerala", "AMBALAPUZHA": "Kerala",
    "CHERTHALA": "Kerala", "ALLEPPEY": "Kerala",
    "ALUVA": "Kerala", "NORTH PARAVUR": "Kerala",
    "KALAMASSERY": "Kerala", "ANGAMALI": "Kerala",
    "MUVATTUPUZHA": "Kerala", "PERUMBAVOOR": "Kerala",
    "KOTHAMANGALAM": "Kerala", "IRINJALAKUDA": "Kerala",
    "GURUVAYUR": "Kerala", "KODUNGALLUR": "Kerala",
    "KUNNAMKULAM": "Kerala", "CHALAKUDY": "Kerala",
    "THRIPPUNITHURA": "Kerala", "TRIPUNITHURA": "Kerala",
    "PARIYARAM": "Kerala", "TALIPARAMBA": "Kerala",
    "IRITTY": "Kerala", "KUTHUPARAMBA": "Kerala",
    "KALPETTA": "Kerala", "SULTHAN BATHERY": "Kerala",
    "MANANTHAVADY": "Kerala", "NILAMBUR": "Kerala",
    "TIRUR": "Kerala", "PONNANI": "Kerala", "TANUR": "Kerala",
    "KONDOTTY": "Kerala", "KARUVARAKUNDU": "Kerala",
    "WANDOOR": "Kerala", "ERANKULAM": "Kerala",
    # Gujarat (more towns)
    "LIMBDI": "Gujarat", "BOTAD": "Gujarat",
    "MAHUVA": "Gujarat", "SAVARKUNDLA": "Gujarat",
    "TALAJA": "Gujarat", "PALITANA": "Gujarat",
    "SIHOR": "Gujarat", "GHOGHA": "Gujarat",
    "DHORAJI": "Gujarat", "JETPUR": "Gujarat",
    "GONDAL": "Gujarat", "UPLETA": "Gujarat",
    "MORBI": "Gujarat", "WANKANER": "Gujarat",
    "DHRANGADHRA": "Gujarat", "HALVAD": "Gujarat",
    "ABDASA": "Gujarat", "GANDHIDHAM": "Gujarat",
    "BHACHAU": "Gujarat", "RAPAR": "Gujarat",
    "MANDVI": "Gujarat", "MUNDRA": "Gujarat",
    "SAMAKHIALI": "Gujarat", "ANJAR": "Gujarat",
    "VADNAGAR": "Gujarat", "KHERALU": "Gujarat",
    "UNJHA": "Gujarat", "SIDHPUR": "Gujarat",
    "PALANPUR": "Gujarat", "DEESA": "Gujarat",
    "THARAD": "Gujarat", "DANTA": "Gujarat",
    "HIMMATNAGAR": "Gujarat", "IDAR": "Gujarat",
    "LUNAWADA": "Gujarat", "SANTRAMPUR": "Gujarat",
    "KALOL": "Gujarat", "KADI": "Gujarat",
    "MEHSANA": "Gujarat", "UNJHA": "Gujarat",
    "KATHLAL": "Gujarat", "KHAMBHAT": "Gujarat",
    "ANKLAV": "Gujarat", "UMRETH": "Gujarat",
    "BORSAD": "Gujarat", "NADIAD": "Gujarat",
    "PETLAD": "Gujarat", "KHEDA": "Gujarat",
    "SAVLI": "Gujarat", "KARJAN": "Gujarat",
    "BODELI": "Gujarat", "SANKHEDA": "Gujarat",
    "UMRAKH": "Gujarat", "BARDOLI": "Gujarat",
    "NAVSARI": "Gujarat", "BILIMORA": "Gujarat",
    "VALSAD": "Gujarat", "DHARAMPUR": "Gujarat",
    "KAPRADA": "Gujarat", "VAPI": "Gujarat",
    # Rajasthan (more towns)
    "SIKAR": "Rajasthan", "JHUNJHUNU": "Rajasthan",
    "CHURU": "Rajasthan", "HANUMANGARH": "Rajasthan",
    "GANGANAGAR": "Rajasthan", "BIKANER": "Rajasthan",
    "CHITTORGARH": "Rajasthan", "BHILWARA": "Rajasthan",
    "RAJSAMAND": "Rajasthan", "NATHDWARA": "Rajasthan",
    "BANSWARA": "Rajasthan", "DUNGARPUR": "Rajasthan",
    "PRATAPGARH": "Rajasthan", "PALI": "Rajasthan",
    "MARWAR": "Rajasthan", "BARMER": "Rajasthan",
    "JAISALMER": "Rajasthan", "BUNDI": "Rajasthan",
    "BARAN": "Rajasthan", "KOTA": "Rajasthan",
    "SAWAI MADHOPUR": "Rajasthan", "KARAULI": "Rajasthan",
    "DHOLPUR": "Rajasthan", "BHARATPUR": "Rajasthan",
    "DEEG": "Rajasthan", "ALWAR": "Rajasthan",
    "LAXMANGARH": "Rajasthan", "DUNDLOD": "Rajasthan",
    "DAUSA": "Rajasthan", "TONK": "Rajasthan",
    "MALPURA": "Rajasthan",
    # Madhya Pradesh (more towns)
    "UJJAIN": "Madhya Pradesh", "RATLAM": "Madhya Pradesh",
    "MANDSAUR": "Madhya Pradesh", "NEEMUCH": "Madhya Pradesh",
    "NIMBAHERA": "Madhya Pradesh", "JHABUA": "Madhya Pradesh",
    "ALIRAJPUR": "Madhya Pradesh", "BARWANI": "Madhya Pradesh",
    "KHARGONE": "Madhya Pradesh", "KHANDWA": "Madhya Pradesh",
    "BURHANPUR": "Madhya Pradesh", "BETUL": "Madhya Pradesh",
    "HOSHANGABAD": "Madhya Pradesh", "ITARSI": "Madhya Pradesh",
    "RAISEN": "Madhya Pradesh", "VIDISHA": "Madhya Pradesh",
    "SEHORE": "Madhya Pradesh", "DEWAS": "Madhya Pradesh",
    "SHAJAPUR": "Madhya Pradesh", "AGAR": "Madhya Pradesh",
    "MORENA": "Madhya Pradesh", "BHIND": "Madhya Pradesh",
    "DATIA": "Madhya Pradesh", "SHIVPURI": "Madhya Pradesh",
    "GUNA": "Madhya Pradesh", "ASHOKNAGAR": "Madhya Pradesh",
    "TIKAMGARH": "Madhya Pradesh", "CHHATARPUR": "Madhya Pradesh",
    "PANNA": "Madhya Pradesh", "DAMOH": "Madhya Pradesh",
    "SAGAR": "Madhya Pradesh", "REHLI": "Madhya Pradesh",
    "SATNA": "Madhya Pradesh", "REWA": "Madhya Pradesh",
    "MAIHAR": "Madhya Pradesh", "NAGOD": "Madhya Pradesh",
    "SIDHI": "Madhya Pradesh", "SINGRAULI": "Madhya Pradesh",
    "SHAHDOL": "Madhya Pradesh", "UMARIA": "Madhya Pradesh",
    "ANUPPUR": "Madhya Pradesh", "DINDORI": "Madhya Pradesh",
    "MANDLA": "Madhya Pradesh", "NARSINGHPUR": "Madhya Pradesh",
    "JABALPUR": "Madhya Pradesh",
    # Punjab (more towns)
    "MOGA": "Punjab", "FAZILKA": "Punjab",
    "ABOHAR": "Punjab", "FIROZEPUR": "Punjab",
    "JALALABAD": "Punjab", "ZIRA": "Punjab",
    "MANSA": "Punjab", "MAUR": "Punjab",
    "MALOUT": "Punjab", "GIDDERBAHA": "Punjab",
    "SUNAM": "Punjab", "LEHRAGAGA": "Punjab",
    "SANGRUR": "Punjab", "DHURI": "Punjab",
    "BARNALA": "Punjab", "TAPA": "Punjab",
    "RAMPURA PHUL": "Punjab", "BUDHLADA": "Punjab",
    "NAWANSHAHR": "Punjab", "NAWAN SHAHR": "Punjab",
    "ROPAR": "Punjab", "ANANDPUR SAHIB": "Punjab",
    "MORINDA": "Punjab", "CHAMKAUR SAHIB": "Punjab",
    "FATEHGARH SAHIB": "Punjab", "SIRHIND": "Punjab",
    "KHANNA": "Punjab", "MANDI GOBINDGARH": "Punjab",
    "SAMRALA": "Punjab", "MACHHIWARA": "Punjab",
    "PHILLAUR": "Punjab", "NAKODAR": "Punjab",
    "KAPURTHALA": "Punjab", "PHAGWARA": "Punjab",
    "DASUYA": "Punjab", "MUKERIAN": "Punjab",
    "HOSHIARPUR": "Punjab", "DASUA": "Punjab",
    "BATALA": "Punjab", "GURDASPUR": "Punjab",
    "DINANAGAR": "Punjab", "DERA BABA NANAK": "Punjab",
    "PATHANKOT": "Punjab", "GURDASPUR": "Punjab",
    # Haryana (more towns)
    "PALWAL": "Haryana", "HODAL": "Haryana",
    "FARIDABAD": "Haryana", "BALLABHGARH": "Haryana",
    "PATAUDI": "Haryana", "MEWAT": "Haryana",
    "NUHM": "Haryana", "NUBM": "Haryana",
    "REWARI": "Haryana", "DHARUHERA": "Haryana",
    "BAWAL": "Haryana", "ATELI": "Haryana",
    "NARNAUL": "Haryana", "MAHENDRAGARH": "Haryana",
    "BHIWANI": "Haryana", "LOHARU": "Haryana",
    "TOSHAM": "Haryana", "CHARKHI DADRI": "Haryana",
    "JHAJJAR": "Haryana", "BAHADURGARH": "Haryana",
    "ROHTAK": "Haryana", "SAMPLA": "Haryana",
    "GOHANA": "Haryana", "SONIPAT": "Haryana",
    "KUNDLI": "Haryana", "PANIPAT": "Haryana",
    "KARNAL": "Haryana", "KAITHAL": "Haryana",
    "PEHOWA": "Haryana", "KURUKSHETRA": "Haryana",
    "SHAHABAD": "Haryana", "THANESAR": "Haryana",
    "LADWA": "Haryana", "AMBALA": "Haryana",
    "BARARA": "Haryana", "YAMUNANAGAR": "Haryana",
    "JAGADHRI": "Haryana", "BILASPUR": "Haryana",
    "HISAR": "Haryana", "FATEHABAD": "Haryana",
    "SIRSA": "Haryana", "ELLENABAD": "Haryana",
    "NARWANA": "Haryana", "JIND": "Haryana",
    "SAFIDON": "Haryana", "NILOKHERI": "Haryana",
    # Uttarakhand (more towns)
    "RISHIKESH": "Uttarakhand", "KOTDWARA": "Uttarakhand",
    "LANSDOWNE": "Uttarakhand", "PAURI": "Uttarakhand",
    "SRINAGAR GARHWAL": "Uttarakhand",
    "CHAMOLI": "Uttarakhand", "GOPESHWAR": "Uttarakhand",
    "KEDARNATH": "Uttarakhand", "RUDRAPRAYAG": "Uttarakhand",
    "AGASTYAMUNI": "Uttarakhand",
    "TEHRI": "Uttarakhand", "CHAMBA": "Uttarakhand",
    "NEW TEHRI": "Uttarakhand",
    "UTTARKASHI": "Uttarakhand", "BHATWARI": "Uttarakhand",
    "DEOPRAYAG": "Uttarakhand",
    "NAINITAL": "Uttarakhand", "BHIMTAL": "Uttarakhand",
    "RAMNAGAR": "Uttarakhand", "KASHIPUR": "Uttarakhand",
    "JASPUR": "Uttarakhand", "KICHHA": "Uttarakhand",
    "SITARGANJ": "Uttarakhand", "KHATIMA": "Uttarakhand",
    "TANAKPUR": "Uttarakhand", "CHAMPAWAT": "Uttarakhand",
    "PITHORAGARH": "Uttarakhand",
    "LOHAGHAT": "Uttarakhand", "BAGESHWAR": "Uttarakhand",
    "ALMORA": "Uttarakhand",
    "VIKASNAGAR": "Uttarakhand",
    "DEHRADUN": "Uttarakhand", "HARIDWAR": "Uttarakhand",
    "ROORKEE": "Uttarakhand", "MUZZAFARNAGAR": "Uttarakhand",
    # Himachal Pradesh (more towns)
    "MANDI": "Himachal Pradesh", "KULLU": "Himachal Pradesh",
    "MANALI": "Himachal Pradesh", "SOLAN": "Himachal Pradesh",
    "KASAULI": "Himachal Pradesh", "PARWANOO": "Himachal Pradesh",
    "BADDI": "Himachal Pradesh", "NALAGARH": "Himachal Pradesh",
    "BILASPUR HP": "Himachal Pradesh",
    "UNA": "Himachal Pradesh", "HAMIRPUR HP": "Himachal Pradesh",
    "SUJANPUR": "Himachal Pradesh",
    "CHAMBA": "Himachal Pradesh",
    "DHARAMSALA": "Himachal Pradesh",
    "PALAMPUR": "Himachal Pradesh",
    "NURPUR": "Himachal Pradesh", "NAGROTA KANGRA": "Himachal Pradesh",
    "SUNDERNAGAR": "Himachal Pradesh",
    # Odisha (more towns)
    "BHUBANESWAR": "Odisha", "CUTTACK": "Odisha",
    "ROURKELA": "Odisha", "BERHAMPUR": "Odisha",
    "BRAHMAPUR": "Odisha", "SAMBALPUR": "Odisha",
    "PURI": "Odisha", "BALASORE": "Odisha",
    "BARIPADA": "Odisha", "BHADRAK": "Odisha",
    "JAJPUR": "Odisha", "KENDRAPARA": "Odisha",
    "DHENKANAL": "Odisha", "KEONJHAR": "Odisha",
    "ANGUL": "Odisha", "TALCHER": "Odisha",
    "JHARSUGUDA": "Odisha", "BARGARH": "Odisha",
    "BOLANGIR": "Odisha", "TITLAGARH": "Odisha",
    "PHULBANI": "Odisha", "KORAPUT": "Odisha",
    "JEYPORE": "Odisha", "NOWRANGPUR": "Odisha",
    "RAYAGADA": "Odisha", "KALAHANDI": "Odisha",
    "BHAWANIPATNA": "Odisha", "MAYURBHANJ": "Odisha",
    "SUNDARGARH": "Odisha", "ROURKELA": "Odisha",
    # West Bengal (more towns)
    "KRISHNANAGAR": "West Bengal",
    "BERHAMPORE": "West Bengal", "LALBAGH": "West Bengal",
    "MALDA": "West Bengal", "ENGLISH BAZAR": "West Bengal",
    "SILIGURI": "West Bengal", "JALPAIGURI": "West Bengal",
    "ALIPURDUAR": "West Bengal", "COOCH BEHAR": "West Bengal",
    "DARJEELING": "West Bengal", "KURSEONG": "West Bengal",
    "MIRIK": "West Bengal",
    "RAIGANJ": "West Bengal", "ISLAMPUR": "West Bengal",
    "DALKHOLA": "West Bengal",
    "BALURGHAT": "West Bengal", "GANGARAMPUR": "West Bengal",
    "DINHATA": "West Bengal",
    "PURULIA": "West Bengal", "BANKURA": "West Bengal",
    "BISHNUPUR": "West Bengal",
    "MIDNAPORE": "West Bengal", "KHARAGPUR": "West Bengal",
    "JHARGRAM": "West Bengal", "TAMLUK": "West Bengal",
    "CONTAI": "West Bengal", "HALDIA": "West Bengal",
    "DIAMOND HARBOUR": "West Bengal",
    # Assam (more towns)
    "DIBRUGARH": "Assam", "JORHAT": "Assam",
    "SIBSAGAR": "Assam", "GOLAGHAT": "Assam",
    "TINSUKIA": "Assam", "DOOM DOOMA": "Assam",
    "BONGAIGAON": "Assam", "KOKRAJHAR": "Assam",
    "DHUBRI": "Assam", "GOALPARA": "Assam",
    "BARPETA": "Assam", "NALBARI": "Assam",
    "KAMRUP": "Assam", "RANGIA": "Assam",
    "KARIMGANJ": "Assam", "HAILAKANDI": "Assam",
    "SILCHAR": "Assam", "LAKHIMPUR": "Assam",
    "DHEMAJI": "Assam", "NORTH LAKHIMPUR": "Assam",
    "NAGAON": "Assam",
    "HOJAI": "Assam", "LANKA": "Assam",
    # Chhattisgarh (more towns)
    "BHILAI": "Chhattisgarh", "DURG": "Chhattisgarh",
    "KORBA": "Chhattisgarh", "BILASPUR CG": "Chhattisgarh",
    "JAGDALPUR": "Chhattisgarh", "RAIGARH": "Chhattisgarh",
    "AMBIKAPUR": "Chhattisgarh", "RAJNANDGAON": "Chhattisgarh",
    "JANJGIR": "Chhattisgarh", "CHAMPA": "Chhattisgarh",
    "KABIRDHAM": "Chhattisgarh", "KAWARDHA": "Chhattisgarh",
    "BALOD": "Chhattisgarh", "DONGARGARH": "Chhattisgarh",
    "BEMETARA": "Chhattisgarh",
    "BHATAPARA": "Chhattisgarh", "TILDA": "Chhattisgarh",
    "MAHASAMUND": "Chhattisgarh",
    "GARIYABAND": "Chhattisgarh",
    "KONDAGAON": "Chhattisgarh",
    "KANKER": "Chhattisgarh",
    "NARAYANPUR": "Chhattisgarh",
    "DANTEWADA": "Chhattisgarh",
    "BIJAPUR CG": "Chhattisgarh",
    "SUKMA": "Chhattisgarh",
    # Jharkhand (more towns)
    "HAZARIBAG": "Jharkhand", "CHATRA": "Jharkhand",
    "KODERMA": "Jharkhand", "GIRIDIH": "Jharkhand",
    "DEOGHAR": "Jharkhand", "GODDA": "Jharkhand",
    "SAHIBGANJ": "Jharkhand", "PAKUR": "Jharkhand",
    "DUMKA": "Jharkhand", "JAMTARA": "Jharkhand",
    "SERAIKELA": "Jharkhand", "CHAIBASA": "Jharkhand",
    "GUMLA": "Jharkhand", "SIMDEGA": "Jharkhand",
    "LOHARDAGA": "Jharkhand", "KHUNTI": "Jharkhand",
    "RAMGARH": "Jharkhand", "NIRSA": "Jharkhand",
    # Bihar (more towns)
    "MUZAFFARPUR": "Bihar", "DARBHANGA": "Bihar",
    "BEGUSARAI": "Bihar", "PURNIA": "Bihar",
    "ARARIA": "Bihar", "KISHANGANJ": "Bihar",
    "SUPAUL": "Bihar", "MADHEPURA": "Bihar",
    "SAHARSA": "Bihar", "MADHUBANI": "Bihar",
    "SITAMARHI": "Bihar", "SHEOHAR": "Bihar",
    "MOTIHARI": "Bihar", "BETIAH": "Bihar",
    "GOPALGANJ": "Bihar", "SIWAN": "Bihar",
    "SARAN": "Bihar", "CHHAPRA": "Bihar",
    "BHOJPUR": "Bihar", "ARRAH": "Bihar",
    "BUXAR": "Bihar", "ROHTAS": "Bihar",
    "SASARAM": "Bihar", "KAIMUR": "Bihar",
    "GAYA": "Bihar", "JEHANABAD": "Bihar",
    "AURANGABAD BIHAR": "Bihar",
    "NAWADA": "Bihar", "NALANDA": "Bihar",
    "RAJGIR": "Bihar", "SHEIKHPURA": "Bihar",
    "LAKHISARAI": "Bihar", "JAMUI": "Bihar",
    "BANKA": "Bihar", "BHAGALPUR": "Bihar",
    "MUNGER": "Bihar", "KHAGARIA": "Bihar",
    "SAMASTIPUR": "Bihar",
    "VAISHALI": "Bihar", "HAJIPUR": "Bihar",
}

from app.core.database import SessionLocal
from app.models.institution import Institution
from sqlalchemy import select, text

db = SessionLocal()
insts = db.execute(
    select(Institution).where(Institution.state.is_(None))
).scalars().all()
total = len(insts)
print(f"Processing {total} institutions...")

# Sort cities by length descending to match longer names first
from_cities = sorted(MORE_CITIES.keys(), key=len, reverse=True)

def infer(name: str) -> str | None:
    upper = name.upper()

    # 1. Abbreviations
    for pattern, state in ABBREVIATIONS.items():
        if re.search(pattern, upper):
            return state

    # 2. Check suffix after last comma: "COLLEGE, PUNE" → Pune
    if "," in name:
        suffix = name.split(",")[-1].strip().upper()
        for city in from_cities:
            if city.upper() == suffix or suffix.startswith(city.upper()):
                return MORE_CITIES[city]

    # 3. Check city names anywhere in name
    for city in from_cities:
        pattern = r'\b' + re.escape(city.upper()) + r'\b'
        if re.search(pattern, upper):
            return MORE_CITIES[city]

    return None

updated = 0
for inst in insts:
    state = infer(inst.name)
    if state:
        inst.state = state
        updated += 1

db.commit()
with_state = db.query(Institution).filter(Institution.state.isnot(None)).count()
rows = db.execute(
    text("SELECT state, COUNT(*) cnt FROM institutions WHERE state IS NOT NULL GROUP BY state ORDER BY cnt DESC LIMIT 28")
).fetchall()
db.close()

print(f"\nUpdated: {updated}")
print(f"Total with state: {with_state} / 4634")
print(f"\nAll states found:")
for s, c in rows:
    print(f"  {s:<35} {c}")
