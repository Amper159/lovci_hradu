import json
import sqlite3

kraje_souradnice = [
    ("Praha", 50.0, 50.18, 14.22, 14.71),
    ("Středočeský", 49.4, 50.5, 13.09, 15.8),
    ("Jihočeský", 48.55, 49.3, 13.0, 15.8),
    ("Plzeňský", 49.0, 50.2, 12.0, 14.0),
    ("Karlovarský", 50.0, 50.6, 12.1, 12.9),
    ("Ústecký", 50.4, 51.0, 13.4, 14.7),
    ("Liberecký", 50.3, 50.8, 14.3, 15.8),
    ("Královéhradecký", 50.0, 50.7, 15.3, 16.8),
    ("Pardubický", 49.5, 50.2, 15.3, 16.8),
    ("Vysočina", 49.0, 49.8, 15.3, 16.8),
    ("Jihomoravský", 48.5, 49.5, 16.0, 17.7),
    ("Olomoucký", 49.3, 50.3, 16.8, 18.5),
    ("Moravskoslezský", 49.3, 50.0, 17.5, 18.9),
    ("Zlínský", 48.6, 49.4, 17.2, 18.5),
]

# Seznam klíčových slov a známých zřícenin
ZRICENINY_KEYWORDS = [
    "zřícenina", "zricenina", "zříceniny", "torzo", "ruin", "zříceného",
    "trosky", "hazmburk", "hukvaldy", "rabí", "raby", "bezděz", "bezdaz", 
    "dívčí kámen", "divci kamen", "kor适当", "střekov", "strekov", "kamýk",
    "krakovec", "valdštejn", "valdstejn", "sirotčí hrádek", "dívčí hrady",
    "lhota", "veveří", "pomezí", "frymburk", "helfštýn", "helfstyn"
]

def najdi_kraj(lat, lon):
    if not lat or not lon: return "Česko"
    for kraj, min_lat, max_lat, min_lng, max_lng in kraje_souradnice:
        if min_lat <= lat <= max_lat and min_lng <= lon <= max_lng:
            return kraj
    return "Česko"

def urci_typ(nazev, popis="", foto=""):
    # Důkladný textový řetězec spojený ze všech dostupných polí
    full_text = f"{nazev} {popis} {foto}".lower()
    
    # 1. Kontrola zříceniny
    if any(kw in full_text for kw in ZRICENINY_KEYWORDS):
        return "zricenina"
    
    # 2. Kontrola zámku
    elif "zámek" in full_text or "zamek" in full_text:
        return "zamek"
    
    # 3. Výchozí je hrad
    else:
        return "hrad"

print("1. Načítám JSON...")
with open("hrady_data.json", "r", encoding="utf-8") as f:
    hrady = json.load(f)

pocet_zricenin = 0
pocet_zamku = 0
pocet_hradu = 0

print(f"2. Analýza typů pro {len(hrady)} památek...")
for hrad in hrady:
    lon = hrad.get("lon") if hrad.get("lon") is not None else hrad.get("lng", 0)
    lat = hrad.get("lat", 0)
    nazev = hrad.get("nazev", "")
    popis = hrad.get("popis", "")
    foto = hrad.get("foto", "")
    
    hrad["kraj"] = najdi_kraj(lat, lon)
    hrad["typ"] = urci_typ(nazev, popis, foto)
    
    if hrad["typ"] == "zricenina":
        pocet_zricenin += 1
        hrad["auto"] = 0
        hrad["kocarek"] = 0
    elif hrad["typ"] == "zamek":
        pocet_zamku += 1
        hrad["auto"] = 1
        hrad["kocarek"] = 1
    else:
        pocet_hradu += 1
        hrad["auto"] = 1
        hrad["kocarek"] = 0

print(f"   📊 Výsledek rozřazení:")
print(f"      • Zámky: {pocet_zamku}")
print(f"      • Hrady: {pocet_hradu}")
print(f"      • Zříceniny: {pocet_zricenin}")

print("3. Ukládám opravený JSON...")
with open("hrady_data.json", "w", encoding="utf-8") as f:
    json.dump(hrady, f, ensure_ascii=False, indent=4)

print("4. Připojuji k DB a obnovuji tabulku 'pamatky'...")
conn = sqlite3.connect("databaze.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS pamatky")
cursor.execute('''
    CREATE TABLE pamatky (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nazev TEXT,
        typ TEXT,
        kraj TEXT,
        lat REAL,
        lon REAL,
        foto TEXT,
        auto INTEGER DEFAULT 0,
        kocarek INTEGER DEFAULT 0
    )
''')

for hrad in hrady:
    cursor.execute("""
        INSERT INTO pamatky (nazev, typ, kraj, lat, lon, foto, auto, kocarek)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        hrad.get("nazev"),
        hrad.get("typ"),
        hrad.get("kraj"),
        hrad.get("lat"),
        hrad.get("lon") if hrad.get("lon") is not None else hrad.get("lng"),
        hrad.get("foto", ""),
        hrad.get("auto", 0),
        hrad.get("kocarek", 0)
    ))

conn.commit()
conn.close()
print("✅ Databáze byla úspěšně aktualizována!")