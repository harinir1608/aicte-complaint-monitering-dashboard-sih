"""Fast state enrichment using a single compiled regex pattern."""
import sys, re
sys.path.insert(0, '.')

CITY_STATE = {
    # Maharashtra
    "PUNE":["Maharashtra"],"PIMPRI":["Maharashtra"],"MUMBAI":["Maharashtra"],"BOMBAY":["Maharashtra"],
    "NAVI MUMBAI":["Maharashtra"],"THANE":["Maharashtra"],"NASHIK":["Maharashtra"],
    "AURANGABAD":["Maharashtra"],"NAGPUR":["Maharashtra"],"SOLAPUR":["Maharashtra"],
    "KOLHAPUR":["Maharashtra"],"SATARA":["Maharashtra"],"SANGLI":["Maharashtra"],
    "NANDED":["Maharashtra"],"JALNA":["Maharashtra"],"AMRAVATI":["Maharashtra"],
    "AKOLA":["Maharashtra"],"WARDHA":["Maharashtra"],"YAVATMAL":["Maharashtra"],
    "GONDIA":["Maharashtra"],"CHANDRAPUR":["Maharashtra"],"BHANDARA":["Maharashtra"],
    "DHULE":["Maharashtra"],"JALGAON":["Maharashtra"],"PALGHAR":["Maharashtra"],
    "OSMANABAD":["Maharashtra"],"BHUSAWAL":["Maharashtra"],"ICHALKARANJI":["Maharashtra"],
    "MIRAJ":["Maharashtra"],"KOPARGAON":["Maharashtra"],"PANDHARPUR":["Maharashtra"],
    "KARAD":["Maharashtra"],"ASHTA":["Maharashtra"],"SHAHADA":["Maharashtra"],
    "NILANGA":["Maharashtra"],"UDGIR":["Maharashtra"],"VITA":["Maharashtra"],
    "SHIRPUR":["Maharashtra"],"BARAMATI":["Maharashtra"],"JAMNER":["Maharashtra"],
    "WARANANAGAR":["Maharashtra"],"LATUR":["Maharashtra"],"AHMEDNAGAR":["Maharashtra"],
    # Karnataka
    "BANGALORE":["Karnataka"],"BENGALURU":["Karnataka"],"MYSORE":["Karnataka"],
    "MYSURU":["Karnataka"],"HUBLI":["Karnataka"],"DHARWAD":["Karnataka"],
    "MANGALORE":["Karnataka"],"MANGALURU":["Karnataka"],"BELGAUM":["Karnataka"],
    "BELAGAVI":["Karnataka"],"DAVANGERE":["Karnataka"],"BELLARY":["Karnataka"],
    "BIJAPUR":["Karnataka"],"VIJAYAPURA":["Karnataka"],"GULBARGA":["Karnataka"],
    "KALABURAGI":["Karnataka"],"TUMKUR":["Karnataka"],"SHIMOGA":["Karnataka"],
    "SHIVAMOGGA":["Karnataka"],"BIDAR":["Karnataka"],"RAICHUR":["Karnataka"],
    "HASSAN":["Karnataka"],"UDUPI":["Karnataka"],"CHITRADURGA":["Karnataka"],
    "KOLAR":["Karnataka"],"BAGALKOT":["Karnataka"],"HUMNABAD":["Karnataka"],
    "MANDYA":["Karnataka"],"NITTE":["Karnataka"],"BANTWAL":["Karnataka"],
    "YADGIR":["Karnataka"],"CHIKKABALLAPUR":["Karnataka"],"UJIRE":["Karnataka"],
    "CHIKMAGALUR":["Karnataka"],"KODAGU":["Karnataka"],"HARIHAR":["Karnataka"],
    "SHIVAMOGGA":["Karnataka"],"MADDUR":["Karnataka"],"KANAKAPURA":["Karnataka"],
    "LINGASUGUR":["Karnataka"],"KADUR":["Karnataka"],"GULBARGA":["Karnataka"],
    # Tamil Nadu
    "CHENNAI":["Tamil Nadu"],"MADRAS":["Tamil Nadu"],"COIMBATORE":["Tamil Nadu"],
    "MADURAI":["Tamil Nadu"],"TRICHY":["Tamil Nadu"],"TIRUCHIRAPPALLI":["Tamil Nadu"],
    "SALEM":["Tamil Nadu"],"TIRUNELVELI":["Tamil Nadu"],"VELLORE":["Tamil Nadu"],
    "ERODE":["Tamil Nadu"],"TIRUPPUR":["Tamil Nadu"],"DINDIGUL":["Tamil Nadu"],
    "THANJAVUR":["Tamil Nadu"],"NAMAKKAL":["Tamil Nadu"],"KANCHEEPURAM":["Tamil Nadu"],
    "KRISHNAGIRI":["Tamil Nadu"],"DHARMAPURI":["Tamil Nadu"],"PERAMBALUR":["Tamil Nadu"],
    "NAGAPATTINAM":["Tamil Nadu"],"CUDDALORE":["Tamil Nadu"],"PUDUKOTTAI":["Tamil Nadu"],
    "RAMANATHAPURAM":["Tamil Nadu"],"THOOTHUKUDI":["Tamil Nadu"],"TUTICORIN":["Tamil Nadu"],
    "KANYAKUMARI":["Tamil Nadu"],"NAGERCOIL":["Tamil Nadu"],"TIRUVANNAMALAI":["Tamil Nadu"],
    "KUMBAKONAM":["Tamil Nadu"],"KARAIKUDI":["Tamil Nadu"],"SIVAKASI":["Tamil Nadu"],
    "POLLACHI":["Tamil Nadu"],"TAMBARAM":["Tamil Nadu"],"AMBATTUR":["Tamil Nadu"],
    "TIRUVALLUR":["Tamil Nadu"],"TIRUVARUR":["Tamil Nadu"],"SIVAGANGA":["Tamil Nadu"],
    "VILLUPURAM":["Tamil Nadu"],"VIRUDHUNAGAR":["Tamil Nadu"],"THIRUNINRAVUR":["Tamil Nadu"],
    "BHAVANI":["Tamil Nadu"],"KOVILPATTI":["Tamil Nadu"],"KARAIKAL":["Puducherry"],
    # Telangana
    "HYDERABAD":["Telangana"],"WARANGAL":["Telangana"],"NIZAMABAD":["Telangana"],
    "KARIMNAGAR":["Telangana"],"KHAMMAM":["Telangana"],"NALGONDA":["Telangana"],
    "ADILABAD":["Telangana"],"MAHABUBNAGAR":["Telangana"],"MEDAK":["Telangana"],
    "SECUNDERABAD":["Telangana"],"SANGAREDDY":["Telangana"],"ZAHEERABAD":["Telangana"],
    "SIDDIPET":["Telangana"],"YADADRI":["Telangana"],"RANGAREDDY":["Telangana"],
    # Andhra Pradesh
    "VIJAYAWADA":["Andhra Pradesh"],"VISAKHAPATNAM":["Andhra Pradesh"],
    "VIZAG":["Andhra Pradesh"],"GUNTUR":["Andhra Pradesh"],"NELLORE":["Andhra Pradesh"],
    "KURNOOL":["Andhra Pradesh"],"TIRUPATI":["Andhra Pradesh"],"KADAPA":["Andhra Pradesh"],
    "ANANTAPUR":["Andhra Pradesh"],"VIZIANAGARAM":["Andhra Pradesh"],
    "SRIKAKULAM":["Andhra Pradesh"],"BHIMAVARAM":["Andhra Pradesh"],
    "RAJAHMUNDRY":["Andhra Pradesh"],"ELURU":["Andhra Pradesh"],
    "MACHILIPATNAM":["Andhra Pradesh"],"KAKINADA":["Andhra Pradesh"],
    "GUDUR":["Andhra Pradesh"],"PONNUR":["Andhra Pradesh"],"TENALI":["Andhra Pradesh"],
    "NARASARAOPETA":["Andhra Pradesh"],"KAVALI":["Andhra Pradesh"],
    "PRODDATUR":["Andhra Pradesh"],"NANDYAL":["Andhra Pradesh"],
    "ONGOLE":["Andhra Pradesh"],"CHITTOOR":["Andhra Pradesh"],
    # Uttar Pradesh
    "LUCKNOW":["Uttar Pradesh"],"KANPUR":["Uttar Pradesh"],"AGRA":["Uttar Pradesh"],
    "VARANASI":["Uttar Pradesh"],"ALLAHABAD":["Uttar Pradesh"],"PRAYAGRAJ":["Uttar Pradesh"],
    "MEERUT":["Uttar Pradesh"],"GHAZIABAD":["Uttar Pradesh"],"NOIDA":["Uttar Pradesh"],
    "GREATER NOIDA":["Uttar Pradesh"],"MATHURA":["Uttar Pradesh"],"ALIGARH":["Uttar Pradesh"],
    "MORADABAD":["Uttar Pradesh"],"BAREILLY":["Uttar Pradesh"],"GORAKHPUR":["Uttar Pradesh"],
    "FAIZABAD":["Uttar Pradesh"],"SAHARANPUR":["Uttar Pradesh"],"JHANSI":["Uttar Pradesh"],
    "FIROZABAD":["Uttar Pradesh"],"ETAWAH":["Uttar Pradesh"],"UNNAO":["Uttar Pradesh"],
    "JAUNPUR":["Uttar Pradesh"],"AZAMGARH":["Uttar Pradesh"],"MIRZAPUR":["Uttar Pradesh"],
    "SONEBHADRA":["Uttar Pradesh"],"BANDA":["Uttar Pradesh"],"LAKHIMPUR":["Uttar Pradesh"],
    "HARDOI":["Uttar Pradesh"],"MODINAGAR":["Uttar Pradesh"],"ORAI":["Uttar Pradesh"],
    "SHIKOHABAD":["Uttar Pradesh"],"BIJNOR":["Uttar Pradesh"],"RAMPUR":["Uttar Pradesh"],
    "SITAPUR":["Uttar Pradesh"],"BULANDSHAHR":["Uttar Pradesh"],"MUZAFFARNAGAR":["Uttar Pradesh"],
    "HAPUR":["Uttar Pradesh"],"FARRUKHABAD":["Uttar Pradesh"],"MAINPURI":["Uttar Pradesh"],
    # Rajasthan
    "JAIPUR":["Rajasthan"],"JODHPUR":["Rajasthan"],"UDAIPUR":["Rajasthan"],
    "KOTA":["Rajasthan"],"AJMER":["Rajasthan"],"BIKANER":["Rajasthan"],
    "ALWAR":["Rajasthan"],"BHARATPUR":["Rajasthan"],"SIKAR":["Rajasthan"],
    "PALI":["Rajasthan"],"NAGAUR":["Rajasthan"],"BHILWARA":["Rajasthan"],
    "CHURU":["Rajasthan"],"JHUNJHUNU":["Rajasthan"],"DAUSA":["Rajasthan"],
    "ABU ROAD":["Rajasthan"],"SIROHI":["Rajasthan"],"JAISALMER":["Rajasthan"],
    "BARMER":["Rajasthan"],"CHITTORGARH":["Rajasthan"],"BUNDI":["Rajasthan"],
    "JHALAWAR":["Rajasthan"],"DUNLOD":["Rajasthan"],"TONK":["Rajasthan"],
    # Gujarat
    "AHMEDABAD":["Gujarat"],"SURAT":["Gujarat"],"VADODARA":["Gujarat"],
    "BARODA":["Gujarat"],"RAJKOT":["Gujarat"],"GANDHINAGAR":["Gujarat"],
    "BHAVNAGAR":["Gujarat"],"JAMNAGAR":["Gujarat"],"JUNAGADH":["Gujarat"],
    "ANAND":["Gujarat"],"MEHSANA":["Gujarat"],"SURENDRANAGAR":["Gujarat"],
    "NAVSARI":["Gujarat"],"VALSAD":["Gujarat"],"VAPI":["Gujarat"],
    "BHARUCH":["Gujarat"],"PATAN":["Gujarat"],"DAHOD":["Gujarat"],
    "GODHRA":["Gujarat"],"VISNAGAR":["Gujarat"],"MODASA":["Gujarat"],
    "SARIGAM":["Gujarat"],"UMRAKH":["Gujarat"],"BARDOLI":["Gujarat"],
    "KEVADIYA":["Gujarat"],"AMRELI":["Gujarat"],"BOTAD":["Gujarat"],
    # Madhya Pradesh
    "BHOPAL":["Madhya Pradesh"],"INDORE":["Madhya Pradesh"],"GWALIOR":["Madhya Pradesh"],
    "JABALPUR":["Madhya Pradesh"],"UJJAIN":["Madhya Pradesh"],"SAGAR":["Madhya Pradesh"],
    "REWA":["Madhya Pradesh"],"SATNA":["Madhya Pradesh"],"DHAR":["Madhya Pradesh"],
    "RATLAM":["Madhya Pradesh"],"CHHINDWARA":["Madhya Pradesh"],"KHANDWA":["Madhya Pradesh"],
    "VIDISHA":["Madhya Pradesh"],"RAISEN":["Madhya Pradesh"],"ITARSI":["Madhya Pradesh"],
    "KATNI":["Madhya Pradesh"],"SEONI":["Madhya Pradesh"],"BALAGHAT":["Madhya Pradesh"],
    "BETUL":["Madhya Pradesh"],"BURHANPUR":["Madhya Pradesh"],"MORENA":["Madhya Pradesh"],
    "SHIVPURI":["Madhya Pradesh"],"DEWAS":["Madhya Pradesh"],"MANDSAUR":["Madhya Pradesh"],
    "NEEMUCH":["Madhya Pradesh"],"BANMORE":["Madhya Pradesh"],"SHAHDOL":["Madhya Pradesh"],
    "ANUPPUR":["Madhya Pradesh"],"SINGRAULI":["Madhya Pradesh"],
    # Delhi
    "DELHI":["Delhi"],"NEW DELHI":["Delhi"],
    # Punjab
    "AMRITSAR":["Punjab"],"LUDHIANA":["Punjab"],"JALANDHAR":["Punjab"],
    "PATIALA":["Punjab"],"BATHINDA":["Punjab"],"MOHALI":["Punjab"],
    "SANGRUR":["Punjab"],"BARNALA":["Punjab"],"MOGA":["Punjab"],
    "PATHANKOT":["Punjab"],"HOSHIARPUR":["Punjab"],"ROPAR":["Punjab"],
    "FARIDKOT":["Punjab"],"MUKTSAR":["Punjab"],"FEROZEPUR":["Punjab"],
    "KAPURTHALA":["Punjab"],"FATEHGARH SAHIB":["Punjab"],"RUPNAGAR":["Punjab"],
    "GURDASPUR":["Punjab"],"SAS NAGAR":["Punjab"],"BEGOWAL":["Punjab"],
    "BADBAR":["Punjab"],"NAWANSHAHR":["Punjab"],"YAMUNA NAGAR":["Haryana"],
    # Haryana
    "FARIDABAD":["Haryana"],"GURGAON":["Haryana"],"GURUGRAM":["Haryana"],
    "PANIPAT":["Haryana"],"AMBALA":["Haryana"],"ROHTAK":["Haryana"],
    "SONIPAT":["Haryana"],"SONEPAT":["Haryana"],"HISAR":["Haryana"],
    "KARNAL":["Haryana"],"JHAJJAR":["Haryana"],"REWARI":["Haryana"],
    "BHIWANI":["Haryana"],"PALWAL":["Haryana"],"KURUKSHETRA":["Haryana"],
    "SIRSA":["Haryana"],"FATEHABAD":["Haryana"],"YAMUNANAGAR":["Haryana"],
    "KAITHAL":["Haryana"],"JIND":["Haryana"],"PANCHKULA":["Haryana"],
    "MORNI":["Haryana"],"LOHARU":["Haryana"],"MANESAR":["Haryana"],
    "NILOKHERI":["Haryana"],"NARWANA":["Haryana"],
    # Kerala
    "THIRUVANANTHAPURAM":["Kerala"],"TRIVANDRUM":["Kerala"],"KOCHI":["Kerala"],
    "ERNAKULAM":["Kerala"],"KOZHIKODE":["Kerala"],"CALICUT":["Kerala"],
    "THRISSUR":["Kerala"],"KOLLAM":["Kerala"],"KANNUR":["Kerala"],
    "MALAPPURAM":["Kerala"],"PALAKKAD":["Kerala"],"KOTTAYAM":["Kerala"],
    "KASARAGOD":["Kerala"],"ALAPPUZHA":["Kerala"],"IDUKKI":["Kerala"],
    "WAYANAD":["Kerala"],"ATTINGAL":["Kerala"],"KOTHAMANGALAM":["Kerala"],
    "PERINTHALMANNA":["Kerala"],"KUTTIKKANAM":["Kerala"],"PERUMON":["Kerala"],
    "PATTOOR":["Kerala"],"MATTANUR":["Kerala"],"PALAI":["Kerala"],
    "CHANGANACHERRY":["Kerala"],"PERUMBAVOOR":["Kerala"],"MEENANGADI":["Kerala"],
    "PURAPPUZHA":["Kerala"],"THRIPRAYAR":["Kerala"],"KADUTHURUTHY":["Kerala"],
    "VENNIKULAM":["Kerala"],"TAVANUR":["Kerala"],"MUVATTUPUZHA":["Kerala"],
    # West Bengal
    "KOLKATA":["West Bengal"],"CALCUTTA":["West Bengal"],"HOWRAH":["West Bengal"],
    "DURGAPUR":["West Bengal"],"ASANSOL":["West Bengal"],"SILIGURI":["West Bengal"],
    "KHARAGPUR":["West Bengal"],"HALDIA":["West Bengal"],"BARDHAMAN":["West Bengal"],
    "BANKURA":["West Bengal"],"PURULIA":["West Bengal"],"MALDA":["West Bengal"],
    "MURSHIDABAD":["West Bengal"],"NADIA":["West Bengal"],"JALPAIGURI":["West Bengal"],
    "BARUIPUR":["West Bengal"],"KALYANI":["West Bengal"],"BURDWAN":["West Bengal"],
    "DUMKAL":["West Bengal"],"TUFANGANJ":["West Bengal"],"CONTAI":["West Bengal"],
    "BUDGE BUDGE":["West Bengal"],"KOLAGHAT":["West Bengal"],"JIAGANJ":["West Bengal"],
    "GANGARAMPUR":["West Bengal"],"BANIPUR":["West Bengal"],"BATANAGAR":["West Bengal"],
    "HOOGHLY":["West Bengal"],"BALURGHAT":["West Bengal"],"TAMLUK":["West Bengal"],
    # Bihar
    "PATNA":["Bihar"],"GAYA":["Bihar"],"BHAGALPUR":["Bihar"],"MUZAFFARPUR":["Bihar"],
    "DARBHANGA":["Bihar"],"BEGUSARAI":["Bihar"],"PURNIA":["Bihar"],
    "ARRAH":["Bihar"],"MOTIHARI":["Bihar"],"SITAMARHI":["Bihar"],
    "CHHAPRA":["Bihar"],"HAJIPUR":["Bihar"],"KATIHAR":["Bihar"],"SAMASTIPUR":["Bihar"],
    # Jharkhand
    "RANCHI":["Jharkhand"],"JAMSHEDPUR":["Jharkhand"],"DHANBAD":["Jharkhand"],
    "BOKARO":["Jharkhand"],"HAZARIBAG":["Jharkhand"],"DEOGHAR":["Jharkhand"],
    "GIRIDIH":["Jharkhand"],"RAMGARH":["Jharkhand"],"DUMKA":["Jharkhand"],
    "CHAIBASA":["Jharkhand"],"NIRSA":["Jharkhand"],
    # Odisha
    "BHUBANESWAR":["Odisha"],"CUTTACK":["Odisha"],"ROURKELA":["Odisha"],
    "BERHAMPUR":["Odisha"],"SAMBALPUR":["Odisha"],"PURI":["Odisha"],
    "BALASORE":["Odisha"],"BARIPADA":["Odisha"],"KORAPUT":["Odisha"],
    "SUNDARGARH":["Odisha"],"JHARSUGUDA":["Odisha"],"BHADRAK":["Odisha"],
    "SALIPUR":["Odisha"],"KALUNGA":["Odisha"],"PHULBANI":["Odisha"],
    # Chhattisgarh
    "RAIPUR":["Chhattisgarh"],"BHILAI":["Chhattisgarh"],"DURG":["Chhattisgarh"],
    "BILASPUR":["Chhattisgarh"],"KORBA":["Chhattisgarh"],"JAGDALPUR":["Chhattisgarh"],
    "RAJNANDGAON":["Chhattisgarh"],"RAIGARH":["Chhattisgarh"],"AMBIKAPUR":["Chhattisgarh"],
    "KABIRDHAM":["Chhattisgarh"],"JANJGIR":["Chhattisgarh"],
    # Uttarakhand
    "DEHRADUN":["Uttarakhand"],"HARIDWAR":["Uttarakhand"],"ROORKEE":["Uttarakhand"],
    "NAINITAL":["Uttarakhand"],"HALDWANI":["Uttarakhand"],"RUDRAPUR":["Uttarakhand"],
    "KOTDWARA":["Uttarakhand"],"ALMORA":["Uttarakhand"],"KASHIPUR":["Uttarakhand"],
    "RISHIKESH":["Uttarakhand"],"DWARAHAT":["Uttarakhand"],"BHIMTAL":["Uttarakhand"],
    "KOTABAGH":["Uttarakhand"],"VIKASNAGAR":["Uttarakhand"],"GOPESHWAR":["Uttarakhand"],
    # Himachal Pradesh
    "SHIMLA":["Himachal Pradesh"],"DHARAMSHALA":["Himachal Pradesh"],
    "MANDI":["Himachal Pradesh"],"SOLAN":["Himachal Pradesh"],"UNA":["Himachal Pradesh"],
    "HAMIRPUR":["Himachal Pradesh"],"KULLU":["Himachal Pradesh"],
    "NAGGAR":["Himachal Pradesh"],"KANGRA":["Himachal Pradesh"],"ROHRU":["Himachal Pradesh"],
    "SUNDERNAGAR":["Himachal Pradesh"],"PALAMPUR":["Himachal Pradesh"],
    # Jammu & Kashmir
    "SRINAGAR":["Jammu & Kashmir"],"JAMMU":["Jammu & Kashmir"],
    "ANANTNAG":["Jammu & Kashmir"],"BARAMULLA":["Jammu & Kashmir"],
    "BUDGAM":["Jammu & Kashmir"],"KULGAM":["Jammu & Kashmir"],
    "BANDIPORA":["Jammu & Kashmir"],"DODA":["Jammu & Kashmir"],
    "KATHUA":["Jammu & Kashmir"],"GANDERBAL":["Jammu & Kashmir"],
    # Assam
    "GUWAHATI":["Assam"],"DIBRUGARH":["Assam"],"JORHAT":["Assam"],
    "SILCHAR":["Assam"],"TEZPUR":["Assam"],"NAGAON":["Assam"],
    # Other North-East
    "AGARTALA":["Tripura"],"IMPHAL":["Manipur"],"AIZAWL":["Mizoram"],
    "SHILLONG":["Meghalaya"],"KOHIMA":["Nagaland"],"ATOIZU":["Nagaland"],
    "ITANAGAR":["Arunachal Pradesh"],"PASIGHAT":["Arunachal Pradesh"],
    # Goa
    "PANAJI":["Goa"],"MARGAO":["Goa"],"VASCO":["Goa"],"PONDA":["Goa"],
    "BICHOLIM":["Goa"],"CURCHOREM":["Goa"],
    # Chandigarh
    "CHANDIGARH":["Chandigarh"],
    # Pondicherry
    "PONDICHERRY":["Puducherry"],"PUDUCHERRY":["Puducherry"],
}

# Build ONE compiled regex: match any city as a word
# Sort longest first to prefer "NAVI MUMBAI" over "MUMBAI"
sorted_cities = sorted(CITY_STATE.keys(), key=len, reverse=True)
pattern = re.compile(
    r'\b(' + '|'.join(re.escape(c) for c in sorted_cities) + r')\b',
    re.IGNORECASE
)

def infer_state(name: str) -> str | None:
    m = pattern.search(name.upper())
    if m:
        return CITY_STATE[m.group(1).upper()][0]
    return None

# Quick test
tests = [
    ("PUNE INSTITUTE OF TECHNOLOGY", "Maharashtra"),
    ("BANGALORE INSTITUTE OF TECHNOLOGY", "Karnataka"),
    ("DELHI COLLEGE OF ENGINEERING", "Delhi"),
    ("BOMBAY COLLEGE OF PHARMACY", "Maharashtra"),
    ("CALCUTTA BUSINESS SCHOOL", "West Bengal"),
    ("AMRITSAR COLLEGE OF ENGINEERING & TECHNOLOGY, AMRITSAR", "Punjab"),
]
print("Testing pattern matching:")
for name, expected in tests:
    got = infer_state(name)
    status = "OK" if got == expected else f"FAIL (got {got})"
    print(f"  {status}: {name[:50]}")

print()

from app.core.database import SessionLocal
from app.models.institution import Institution
from sqlalchemy import select

db = SessionLocal()
insts = db.execute(select(Institution).where(Institution.state.is_(None))).scalars().all()
print(f"Processing {len(insts)} institutions...")

updated = 0
for inst in insts:
    state = infer_state(inst.name)
    if state:
        inst.state = state
        updated += 1

db.commit()

# Stats
from sqlalchemy import text
with_state = db.query(Institution).filter(Institution.state.isnot(None)).count()
state_counts = db.execute(
    text("SELECT state, COUNT(*) cnt FROM institutions WHERE state IS NOT NULL GROUP BY state ORDER BY cnt DESC LIMIT 20")
).fetchall()
db.close()

print(f"\nUpdated: {updated}")
print(f"Total with state: {with_state} / 4634")
print(f"\nTop states:")
for s, c in state_counts:
    print(f"  {s:<35} {c}")
