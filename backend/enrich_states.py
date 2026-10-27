"""
Enrich institution records with State data.
Uses a comprehensive city/district → state mapping applied to institution names.
"""
import sys, re
sys.path.insert(0, '.')

# ── Comprehensive Indian city/district → state mapping ────────────────────────
CITY_STATE = {
    # Maharashtra
    "PUNE": "Maharashtra", "PIMPRI": "Maharashtra", "CHINCHWAD": "Maharashtra",
    "MUMBAI": "Maharashtra", "BOMBAY": "Maharashtra", "NAVI MUMBAI": "Maharashtra",
    "THANE": "Maharashtra", "NASHIK": "Maharashtra", "AURANGABAD": "Maharashtra",
    "NAGPUR": "Maharashtra", "SOLAPUR": "Maharashtra", "KOLHAPUR": "Maharashtra",
    "SATARA": "Maharashtra", "SANGLI": "Maharashtra", "NANDED": "Maharashtra",
    "AHMEDNAGAR": "Maharashtra", "LATUR": "Maharashtra", "JALNA": "Maharashtra",
    "AMRAVATI": "Maharashtra", "AKOLA": "Maharashtra", "WARDHA": "Maharashtra",
    "YAVATMAL": "Maharashtra", "BULDANA": "Maharashtra", "WASHIM": "Maharashtra",
    "GONDIA": "Maharashtra", "CHANDRAPUR": "Maharashtra", "GADCHIROLI": "Maharashtra",
    "BHANDARA": "Maharashtra", "DHULE": "Maharashtra", "NANDURBAR": "Maharashtra",
    "JALGAON": "Maharashtra", "PALGHAR": "Maharashtra", "RAIGAD": "Maharashtra",
    "RATNAGIRI": "Maharashtra", "SINDHUDURG": "Maharashtra", "OSMANABAD": "Maharashtra",
    "HINGOLI": "Maharashtra", "PARBHANI": "Maharashtra", "BHUSAWAL": "Maharashtra",
    "ICHALKARANJI": "Maharashtra", "MIRAJ": "Maharashtra", "KOPARGAON": "Maharashtra",
    "PANDHARPUR": "Maharashtra", "VITA": "Maharashtra", "SHIRPUR": "Maharashtra",
    "BARAMATI": "Maharashtra", "WARANANAGAR": "Maharashtra", "JAMNER": "Maharashtra",
    "NILANGA": "Maharashtra", "UDGIR": "Maharashtra", "KARAD": "Maharashtra",
    "ASHTA": "Maharashtra", "SHAHADA": "Maharashtra",
    # Karnataka
    "BANGALORE": "Karnataka", "BENGALURU": "Karnataka", "MYSORE": "Karnataka",
    "MYSURU": "Karnataka", "HUBLI": "Karnataka", "DHARWAD": "Karnataka",
    "MANGALORE": "Karnataka", "MANGALURU": "Karnataka", "BELGAUM": "Karnataka",
    "BELAGAVI": "Karnataka", "DAVANGERE": "Karnataka", "BELLARY": "Karnataka",
    "BIJAPUR": "Karnataka", "VIJAYAPURA": "Karnataka", "GULBARGA": "Karnataka",
    "KALABURAGI": "Karnataka", "TUMKUR": "Karnataka", "SHIMOGA": "Karnataka",
    "SHIVAMOGGA": "Karnataka", "BIDAR": "Karnataka", "RAICHUR": "Karnataka",
    "KOPPAL": "Karnataka", "GADAG": "Karnataka", "HASSAN": "Karnataka",
    "CHIKMAGALUR": "Karnataka", "KODAGU": "Karnataka", "UDUPI": "Karnataka",
    "CHITRADURGA": "Karnataka", "KOLAR": "Karnataka", "BAGALKOT": "Karnataka",
    "HUMNABAD": "Karnataka", "ANKOLA": "Karnataka", "SIRSI": "Karnataka",
    "MANDYA": "Karnataka", "NITTE": "Karnataka", "KARJAT": "Karnataka",
    "MOODABIDRI": "Karnataka", "UJIRE": "Karnataka", "BANTWAL": "Karnataka",
    "YADGIR": "Karnataka", "CHIKKABALLAPUR": "Karnataka", "VIJAYANAGAR": "Karnataka",
    # Tamil Nadu
    "CHENNAI": "Tamil Nadu", "MADRAS": "Tamil Nadu", "COIMBATORE": "Tamil Nadu",
    "MADURAI": "Tamil Nadu", "TIRUCHIRAPPALLI": "Tamil Nadu", "TRICHY": "Tamil Nadu",
    "SALEM": "Tamil Nadu", "TIRUNELVELI": "Tamil Nadu", "VELLORE": "Tamil Nadu",
    "ERODE": "Tamil Nadu", "TIRUPPUR": "Tamil Nadu", "DINDIGUL": "Tamil Nadu",
    "THANJAVUR": "Tamil Nadu", "RANIPET": "Tamil Nadu", "SIVAGANGA": "Tamil Nadu",
    "VILLUPURAM": "Tamil Nadu", "VIRUDHUNAGAR": "Tamil Nadu", "NAMAKKAL": "Tamil Nadu",
    "KANCHEEPURAM": "Tamil Nadu", "KRISHNAGIRI": "Tamil Nadu", "DHARMAPURI": "Tamil Nadu",
    "PERAMBALUR": "Tamil Nadu", "ARIYALUR": "Tamil Nadu", "NAGAPATTINAM": "Tamil Nadu",
    "TIRUVARUR": "Tamil Nadu", "CUDDALORE": "Tamil Nadu", "PUDUKOTTAI": "Tamil Nadu",
    "RAMANATHAPURAM": "Tamil Nadu", "THOOTHUKUDI": "Tamil Nadu", "TUTICORIN": "Tamil Nadu",
    "KANYAKUMARI": "Tamil Nadu", "NAGERCOIL": "Tamil Nadu", "TIRUVANNAMALAI": "Tamil Nadu",
    "KUMBAKONAM": "Tamil Nadu", "KARAIKUDI": "Tamil Nadu", "SIVAKASI": "Tamil Nadu",
    "BHAVANI": "Tamil Nadu", "KOVILPATTI": "Tamil Nadu", "POLLACHI": "Tamil Nadu",
    "TAMBARAM": "Tamil Nadu", "AVADI": "Tamil Nadu", "AMBATTUR": "Tamil Nadu",
    "THIRUNINRAVUR": "Tamil Nadu", "TIRUVALLUR": "Tamil Nadu",
    # Telangana
    "HYDERABAD": "Telangana", "WARANGAL": "Telangana", "NIZAMABAD": "Telangana",
    "KARIMNAGAR": "Telangana", "KHAMMAM": "Telangana", "NALGONDA": "Telangana",
    "ADILABAD": "Telangana", "MAHABUBNAGAR": "Telangana", "MEDAK": "Telangana",
    "RANGAREDDY": "Telangana", "SECUNDERABAD": "Telangana", "SANGAREDDY": "Telangana",
    "ZAHEERABAD": "Telangana", "SIDDIPET": "Telangana", "YADADRI": "Telangana",
    # Andhra Pradesh
    "VIJAYAWADA": "Andhra Pradesh", "VISAKHAPATNAM": "Andhra Pradesh",
    "VIZAG": "Andhra Pradesh", "GUNTUR": "Andhra Pradesh", "NELLORE": "Andhra Pradesh",
    "KURNOOL": "Andhra Pradesh", "TIRUPATI": "Andhra Pradesh", "KADAPA": "Andhra Pradesh",
    "ANANTAPUR": "Andhra Pradesh", "VIZIANAGARAM": "Andhra Pradesh",
    "SRIKAKULAM": "Andhra Pradesh", "WEST GODAVARI": "Andhra Pradesh",
    "EAST GODAVARI": "Andhra Pradesh", "KRISHNA": "Andhra Pradesh",
    "PRAKASAM": "Andhra Pradesh", "ONGOLE": "Andhra Pradesh", "CHITTOOR": "Andhra Pradesh",
    "BHIMAVARAM": "Andhra Pradesh", "RAJAHMUNDRY": "Andhra Pradesh",
    "ELURU": "Andhra Pradesh", "MACHILIPATNAM": "Andhra Pradesh",
    "KAKINADA": "Andhra Pradesh", "GUDUR": "Andhra Pradesh", "PONNUR": "Andhra Pradesh",
    "TENALI": "Andhra Pradesh", "NARASARAOPETA": "Andhra Pradesh",
    "AMALAPURAM": "Andhra Pradesh", "KAVALI": "Andhra Pradesh",
    "NANDYAL": "Andhra Pradesh", "PRODDATUR": "Andhra Pradesh",
    # Uttar Pradesh
    "LUCKNOW": "Uttar Pradesh", "KANPUR": "Uttar Pradesh", "AGRA": "Uttar Pradesh",
    "VARANASI": "Uttar Pradesh", "ALLAHABAD": "Uttar Pradesh", "PRAYAGRAJ": "Uttar Pradesh",
    "MEERUT": "Uttar Pradesh", "GHAZIABAD": "Uttar Pradesh", "NOIDA": "Uttar Pradesh",
    "GREATER NOIDA": "Uttar Pradesh", "MATHURA": "Uttar Pradesh", "ALIGARH": "Uttar Pradesh",
    "MORADABAD": "Uttar Pradesh", "BAREILLY": "Uttar Pradesh", "GORAKHPUR": "Uttar Pradesh",
    "FAIZABAD": "Uttar Pradesh", "SAHARANPUR": "Uttar Pradesh", "JHANSI": "Uttar Pradesh",
    "FIROZABAD": "Uttar Pradesh", "ETAWAH": "Uttar Pradesh", "SHAHJAHANPUR": "Uttar Pradesh",
    "RAEBARELI": "Uttar Pradesh", "SITAPUR": "Uttar Pradesh", "BULANDSHAHR": "Uttar Pradesh",
    "MUZAFFARNAGAR": "Uttar Pradesh", "HAPUR": "Uttar Pradesh", "BIJNOR": "Uttar Pradesh",
    "RAMPUR": "Uttar Pradesh", "BADAUN": "Uttar Pradesh", "UNNAO": "Uttar Pradesh",
    "FATEHPUR": "Uttar Pradesh", "PRATAPGARH": "Uttar Pradesh", "SULTANPUR": "Uttar Pradesh",
    "JAUNPUR": "Uttar Pradesh", "GONDA": "Uttar Pradesh", "BALLIA": "Uttar Pradesh",
    "AZAMGARH": "Uttar Pradesh", "BASTI": "Uttar Pradesh", "DEORIA": "Uttar Pradesh",
    "SONEBHADRA": "Uttar Pradesh", "MIRZAPUR": "Uttar Pradesh", "BANDA": "Uttar Pradesh",
    "SHIKOHABAD": "Uttar Pradesh", "LAKHIMPUR": "Uttar Pradesh", "HAMIRPUR": "Uttar Pradesh",
    "HARDOI": "Uttar Pradesh", "FARRUKHABAD": "Uttar Pradesh", "MAINPURI": "Uttar Pradesh",
    "MODINAGAR": "Uttar Pradesh", "ORAI": "Uttar Pradesh", "SAHARANPUR": "Uttar Pradesh",
    "ROORKEE": "Uttarakhand", "DEHRADUN": "Uttarakhand",
    # Rajasthan
    "JAIPUR": "Rajasthan", "JODHPUR": "Rajasthan", "UDAIPUR": "Rajasthan",
    "KOTA": "Rajasthan", "AJMER": "Rajasthan", "BIKANER": "Rajasthan",
    "ALWAR": "Rajasthan", "BHARATPUR": "Rajasthan", "SIKAR": "Rajasthan",
    "PALI": "Rajasthan", "NAGAUR": "Rajasthan", "BHILWARA": "Rajasthan",
    "CHURU": "Rajasthan", "JHUNJHUNU": "Rajasthan", "DAUSA": "Rajasthan",
    "DUNLOD": "Rajasthan", "ABU ROAD": "Rajasthan", "SIROHI": "Rajasthan",
    "JAISALMER": "Rajasthan", "BARMER": "Rajasthan", "CHITTORGARH": "Rajasthan",
    "BUNDI": "Rajasthan", "JHALAWAR": "Rajasthan", "TONK": "Rajasthan",
    # Gujarat
    "AHMEDABAD": "Gujarat", "SURAT": "Gujarat", "VADODARA": "Gujarat",
    "BARODA": "Gujarat", "RAJKOT": "Gujarat", "GANDHINAGAR": "Gujarat",
    "BHAVNAGAR": "Gujarat", "JAMNAGAR": "Gujarat", "JUNAGADH": "Gujarat",
    "ANAND": "Gujarat", "MEHSANA": "Gujarat", "SURENDRANAGAR": "Gujarat",
    "AMRELI": "Gujarat", "NAVSARI": "Gujarat", "VALSAD": "Gujarat",
    "VAPI": "Gujarat", "ANKLESHWAR": "Gujarat", "BHARUCH": "Gujarat",
    "KHEDA": "Gujarat", "PATAN": "Gujarat", "BANASKANTHA": "Gujarat",
    "SABARKANTHA": "Gujarat", "DAHOD": "Gujarat", "GODHRA": "Gujarat",
    "VISNAGAR": "Gujarat", "MODASA": "Gujarat", "SARIGAM": "Gujarat",
    "UMRAKH": "Gujarat", "BARDOLI": "Gujarat", "OLPAD": "Gujarat",
    "KEVADIYA": "Gujarat", "KATHLAL": "Gujarat", "LUNAWADA": "Gujarat",
    # Madhya Pradesh
    "BHOPAL": "Madhya Pradesh", "INDORE": "Madhya Pradesh", "GWALIOR": "Madhya Pradesh",
    "JABALPUR": "Madhya Pradesh", "UJJAIN": "Madhya Pradesh", "SAGAR": "Madhya Pradesh",
    "REWA": "Madhya Pradesh", "SATNA": "Madhya Pradesh", "DHAR": "Madhya Pradesh",
    "RATLAM": "Madhya Pradesh", "CHHINDWARA": "Madhya Pradesh", "KHANDWA": "Madhya Pradesh",
    "KHARGONE": "Madhya Pradesh", "VIDISHA": "Madhya Pradesh", "RAISEN": "Madhya Pradesh",
    "HOSHANGABAD": "Madhya Pradesh", "ITARSI": "Madhya Pradesh", "KATNI": "Madhya Pradesh",
    "SEONI": "Madhya Pradesh", "BALAGHAT": "Madhya Pradesh", "MANDLA": "Madhya Pradesh",
    "NARSINGHPUR": "Madhya Pradesh", "BETUL": "Madhya Pradesh", "BURHANPUR": "Madhya Pradesh",
    "MORENA": "Madhya Pradesh", "SHIVPURI": "Madhya Pradesh", "DEWAS": "Madhya Pradesh",
    "MANDSAUR": "Madhya Pradesh", "NEEMUCH": "Madhya Pradesh", "JHABUA": "Madhya Pradesh",
    "ALIRAJPUR": "Madhya Pradesh", "BANMORE": "Madhya Pradesh", "SHAHDOL": "Madhya Pradesh",
    "ANUPPUR": "Madhya Pradesh", "SINGRAULI": "Madhya Pradesh",
    # Delhi
    "DELHI": "Delhi", "NEW DELHI": "Delhi", "DWARKA": "Delhi",
    # Punjab
    "AMRITSAR": "Punjab", "LUDHIANA": "Punjab", "JALANDHAR": "Punjab",
    "PATIALA": "Punjab", "BATHINDA": "Punjab", "MOHALI": "Punjab",
    "SANGRUR": "Punjab", "BARNALA": "Punjab", "MOGA": "Punjab",
    "PATHANKOT": "Punjab", "HOSHIARPUR": "Punjab", "ROPAR": "Punjab",
    "FARIDKOT": "Punjab", "MUKTSAR": "Punjab", "FEROZEPUR": "Punjab",
    "KAPURTHALA": "Punjab", "FATEHGARH SAHIB": "Punjab", "RUPNAGAR": "Punjab",
    "GURDASPUR": "Punjab", "SAS NAGAR": "Punjab", "BEGOWAL": "Punjab",
    "BADBAR": "Punjab", "POJEWAL": "Punjab", "NAWANSHAHR": "Punjab",
    "KHUNI MAJRA": "Punjab", "YAMUNA NAGAR": "Punjab",
    # Haryana
    "FARIDABAD": "Haryana", "GURGAON": "Haryana", "GURUGRAM": "Haryana",
    "PANIPAT": "Haryana", "AMBALA": "Haryana", "ROHTAK": "Haryana",
    "SONIPAT": "Haryana", "SONEPAT": "Haryana", "HISAR": "Haryana",
    "KARNAL": "Haryana", "JHAJJAR": "Haryana", "REWARI": "Haryana",
    "BHIWANI": "Haryana", "MAHENDRAGARH": "Haryana", "PALWAL": "Haryana",
    "KURUKSHETRA": "Haryana", "SIRSA": "Haryana", "FATEHABAD": "Haryana",
    "YAMUNANAGAR": "Haryana", "KAITHAL": "Haryana", "JIND": "Haryana",
    "PANCHKULA": "Haryana", "MORNI": "Haryana", "LOHARU": "Haryana",
    "MANESAR": "Haryana", "NILOKHERI": "Haryana", "NARWANA": "Haryana",
    # Kerala
    "THIRUVANANTHAPURAM": "Kerala", "TRIVANDRUM": "Kerala", "KOCHI": "Kerala",
    "ERNAKULAM": "Kerala", "KOZHIKODE": "Kerala", "CALICUT": "Kerala",
    "THRISSUR": "Kerala", "KOLLAM": "Kerala", "KANNUR": "Kerala",
    "MALAPPURAM": "Kerala", "PALAKKAD": "Kerala", "KOTTAYAM": "Kerala",
    "KASARAGOD": "Kerala", "PATHANAMTHITTA": "Kerala", "ALAPPUZHA": "Kerala",
    "IDUKKI": "Kerala", "WAYANAD": "Kerala", "ATTINGAL": "Kerala",
    "KOTHAMANGALAM": "Kerala", "PERINTHALMANNA": "Kerala", "TAVANUR": "Kerala",
    "KUTTANAD": "Kerala", "PERUMON": "Kerala", "PATTOOR": "Kerala",
    "EZHUKONE": "Kerala", "VENNIKULAM": "Kerala", "MUVATTUPUZHA": "Kerala",
    "KARUNAGAPPALLY": "Kerala", "KUTTIKKANAM": "Kerala", "EZHIKONE": "Kerala",
    "PURAPPUZHA": "Kerala", "MATTANUR": "Kerala", "PALAI": "Kerala",
    "THODUPUZHA": "Kerala", "MANNANAM": "Kerala", "THRIPRAYAR": "Kerala",
    "KADUTHURUTHY": "Kerala", "PERUMBAVOOR": "Kerala", "MEENANGADI": "Kerala",
    "EZHUKONE": "Kerala", "KODUNGALLUR": "Kerala", "CHANGANACHERRY": "Kerala",
    # West Bengal
    "KOLKATA": "West Bengal", "CALCUTTA": "West Bengal", "HOWRAH": "West Bengal",
    "DURGAPUR": "West Bengal", "ASANSOL": "West Bengal", "SILIGURI": "West Bengal",
    "KHARAGPUR": "West Bengal", "HALDIA": "West Bengal", "MIDNAPORE": "West Bengal",
    "BARDHAMAN": "West Bengal", "BANKURA": "West Bengal", "PURULIA": "West Bengal",
    "MALDA": "West Bengal", "MURSHIDABAD": "West Bengal", "NADIA": "West Bengal",
    "JALPAIGURI": "West Bengal", "COOCH BEHAR": "West Bengal",
    "NORTH 24 PARGANAS": "West Bengal", "SOUTH 24 PARGANAS": "West Bengal",
    "BARUIPUR": "West Bengal", "KALYANI": "West Bengal", "BURDWAN": "West Bengal",
    "DUMKAL": "West Bengal", "TUFANGANJ": "West Bengal", "RANAGHAT": "West Bengal",
    "CONTAI": "West Bengal", "TAMLUK": "West Bengal", "BUDGE BUDGE": "West Bengal",
    "BELDA": "West Bengal", "KOLAGHAT": "West Bengal", "JIAGANJ": "West Bengal",
    "GANGARAMPUR": "West Bengal", "BANKURA": "West Bengal", "BANIPUR": "West Bengal",
    "BATANAGAR": "West Bengal", "HOOGHLY": "West Bengal", "BALURGHAT": "West Bengal",
    # Bihar
    "PATNA": "Bihar", "GAYA": "Bihar", "BHAGALPUR": "Bihar", "MUZAFFARPUR": "Bihar",
    "DARBHANGA": "Bihar", "BEGUSARAI": "Bihar", "PURNIA": "Bihar",
    "ARRAH": "Bihar", "BETTIAH": "Bihar", "MOTIHARI": "Bihar", "SITAMARHI": "Bihar",
    "CHHAPRA": "Bihar", "HAJIPUR": "Bihar", "KATIHAR": "Bihar", "SAMASTIPUR": "Bihar",
    # Jharkhand
    "RANCHI": "Jharkhand", "JAMSHEDPUR": "Jharkhand", "DHANBAD": "Jharkhand",
    "BOKARO": "Jharkhand", "HAZARIBAG": "Jharkhand", "DEOGHAR": "Jharkhand",
    "GIRIDIH": "Jharkhand", "RAMGARH": "Jharkhand", "DUMKA": "Jharkhand",
    "GARHWA": "Jharkhand", "CHAIBASA": "Jharkhand", "NIRSA": "Jharkhand",
    # Odisha
    "BHUBANESWAR": "Odisha", "CUTTACK": "Odisha", "ROURKELA": "Odisha",
    "BERHAMPUR": "Odisha", "SAMBALPUR": "Odisha", "PURI": "Odisha",
    "BALASORE": "Odisha", "BARIPADA": "Odisha", "KORAPUT": "Odisha",
    "SUNDARGARH": "Odisha", "JHARSUGUDA": "Odisha", "KENDUJHAR": "Odisha",
    "KALAHANDI": "Odisha", "BOLANGIR": "Odisha", "PHULBANI": "Odisha",
    "KHURDA": "Odisha", "JAGATSINGHPUR": "Odisha", "DHENKANAL": "Odisha",
    "SALIPUR": "Odisha", "KALUNGA": "Odisha", "BHADRAK": "Odisha",
    # Chhattisgarh
    "RAIPUR": "Chhattisgarh", "BHILAI": "Chhattisgarh", "DURG": "Chhattisgarh",
    "BILASPUR": "Chhattisgarh", "KORBA": "Chhattisgarh", "JAGDALPUR": "Chhattisgarh",
    "RAJNANDGAON": "Chhattisgarh", "RAIGARH": "Chhattisgarh", "AMBIKAPUR": "Chhattisgarh",
    "KABIRDHAM": "Chhattisgarh", "JANJGIR": "Chhattisgarh",
    # Uttarakhand
    "DEHRADUN": "Uttarakhand", "HARIDWAR": "Uttarakhand", "ROORKEE": "Uttarakhand",
    "NAINITAL": "Uttarakhand", "HALDWANI": "Uttarakhand", "RUDRAPUR": "Uttarakhand",
    "KOTDWARA": "Uttarakhand", "ALMORA": "Uttarakhand", "PITHORAGARH": "Uttarakhand",
    "KASHIPUR": "Uttarakhand", "RISHIKESH": "Uttarakhand", "DWARAHAT": "Uttarakhand",
    "BHIMTAL": "Uttarakhand", "KOTABAGH": "Uttarakhand", "SAHIYA": "Uttarakhand",
    "KANALICHHINA": "Uttarakhand", "BEERONKHAL": "Uttarakhand",
    "VIKASNAGAR": "Uttarakhand", "SUNDERPUR": "Uttarakhand", "JAKHANIDHAR": "Uttarakhand",
    "JEGIRSAND": "Uttarakhand", "KALADHUNGI": "Uttarakhand", "GANGOLI": "Uttarakhand",
    "GARHI SHYAMPUR": "Uttarakhand", "GOPESHWAR": "Uttarakhand",
    # Himachal Pradesh
    "SHIMLA": "Himachal Pradesh", "DHARAMSHALA": "Himachal Pradesh",
    "MANDI": "Himachal Pradesh", "SOLAN": "Himachal Pradesh", "UNA": "Himachal Pradesh",
    "HAMIRPUR": "Himachal Pradesh", "BILASPUR": "Himachal Pradesh",
    "KULLU": "Himachal Pradesh", "LAHAUL": "Himachal Pradesh", "SPITI": "Himachal Pradesh",
    "NAGGAR": "Himachal Pradesh", "KANGRA": "Himachal Pradesh", "ROHRU": "Himachal Pradesh",
    "SUNDERNAGAR": "Himachal Pradesh", "PALAMPUR": "Himachal Pradesh",
    # Jammu & Kashmir
    "SRINAGAR": "Jammu & Kashmir", "JAMMU": "Jammu & Kashmir",
    "ANANTNAG": "Jammu & Kashmir", "BARAMULLA": "Jammu & Kashmir",
    "BUDGAM": "Jammu & Kashmir", "KULGAM": "Jammu & Kashmir",
    "BANDIPORA": "Jammu & Kashmir", "DODA": "Jammu & Kashmir",
    "KATHUA": "Jammu & Kashmir", "GANDERBAL": "Jammu & Kashmir",
    # Assam
    "GUWAHATI": "Assam", "DIBRUGARH": "Assam", "JORHAT": "Assam",
    "SILCHAR": "Assam", "TEZPUR": "Assam", "NAGAON": "Assam",
    "DHUBRI": "Assam", "GOALPARA": "Assam", "BARPETA": "Assam",
    "KARIMGANJ": "Assam", "HAILAKANDI": "Assam", "GOLAGHAT": "Assam",
    "AGARTALA": "Tripura",
    # North-East
    "IMPHAL": "Manipur", "AIZAWL": "Mizoram", "SHILLONG": "Meghalaya",
    "KOHIMA": "Nagaland", "ATOIZU": "Nagaland", "ITANAGAR": "Arunachal Pradesh",
    "GANGTOK": "Sikkim", "PASIGHAT": "Arunachal Pradesh",
    # Goa
    "PANAJI": "Goa", "MARGAO": "Goa", "VASCO": "Goa", "PONDA": "Goa",
    "BICHOLIM": "Goa", "CURCHOREM": "Goa", "QUEPEM": "Goa",
    # Pondicherry
    "PONDICHERRY": "Puducherry", "PUDUCHERRY": "Puducherry",
    # Chandigarh
    "CHANDIGARH": "Chandigarh",
    # Andaman & Nicobar
    "PORT BLAIR": "Andaman & Nicobar",
    # Lakshadweep
    "KAVARATTI": "Lakshadweep",
    # Daman & Diu / D&N Haveli
    "DAMAN": "Daman & Diu", "DIU": "Daman & Diu",
    "SILVASSA": "Dadra & Nagar Haveli",
}

# Sort by length descending so longer names match first (e.g., "GREATER NOIDA" before "NOIDA")
SORTED_CITIES = sorted(CITY_STATE.keys(), key=len, reverse=True)

def infer_state(name: str) -> str | None:
    """Try to find a city/district name in the institution name."""
    n = name.upper()
    for city in SORTED_CITIES:
        # Word boundary match — city must be surrounded by non-alphanumeric chars
        pattern = r'(?<![A-Z])' + re.escape(city) + r'(?![A-Z])'
        if re.search(pattern, n):
            return CITY_STATE[city]
    return None

# ── Run enrichment ────────────────────────────────────────────────────────────
from app.core.database import SessionLocal
from app.models.institution import Institution
from sqlalchemy import select

db = SessionLocal()

institutions = db.execute(
    select(Institution).where(Institution.state.is_(None))
).scalars().all()

print(f"Processing {len(institutions)} institutions without state...")

updated = 0
not_found = 0

for inst in institutions:
    state = infer_state(inst.name)
    if state:
        inst.state = state
        updated += 1
    else:
        not_found += 1

db.commit()

# ── Stats ─────────────────────────────────────────────────────────────────────
total_with_state = db.execute(
    select(Institution).where(Institution.state.isnot(None))
).scalars().__len__() if False else db.query(Institution).filter(Institution.state.isnot(None)).count()

from sqlalchemy import func, text
state_counts = db.execute(
    text("SELECT state, COUNT(*) as cnt FROM institutions WHERE state IS NOT NULL GROUP BY state ORDER BY cnt DESC LIMIT 15")
).fetchall()

db.close()

print(f"\nResults:")
print(f"  Matched with state : {updated}")
print(f"  Could not match    : {not_found}")
print(f"  Total with state   : {total_with_state}")
print(f"\nTop states:")
for state, cnt in state_counts:
    print(f"  {state:<30} {cnt}")
