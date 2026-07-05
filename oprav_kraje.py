import json
import sqlite3

# Definice krajů podle GPS souřadnic (přibližné hranice)
# Formát: (název kraje, min_lat, max_lat, min_lng, max_lng)
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

def najdi_kraj(lat, lng):
    """Najde kraj podle GPS souřadnic"""
    for kraj, min_lat, max_lat, min_lng, max_lng in kraje_souradnice:
        if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
            return kraj
    return "Česko"  # Fallback

# Načti JSON
print("1. Načítám JSON...")
with open("hrady_data.json", "r", encoding="utf-8") as f:
    hrady = json.load(f)

print(f"2. Opravuji kraje ({len(hrady)} památek)...")
# Přiřaď správné kraje podle souřadnic
for i, hrad in enumerate(hrady):
    stary_kraj = hrad.get("kraj", "Česko")
    novy_kraj = najdi_kraj(hrad["lat"], hrad["lng"])
    hrad["kraj"] = novy_kraj
    
    if i % 50 == 0:
        print(f"   Zpracováno {i}/{len(hrady)}")

print("3. Ukládám opravený JSON...")
with open("hrady_data.json", "w", encoding="utf-8") as f:
    json.dump(hrady, f, ensure_ascii=False, indent=4)

print("4. Naplňuji databázi znovu...")
conn = sqlite3.connect("databaze.db")
cursor = conn.cursor()
cursor.execute("DELETE FROM pamatky")

for i, hrad in enumerate(hrady):
    dostupny_auto = 1 if hrad.get("typ") != "zricenina" else 0
    dostupny_kocárek = 1 if hrad.get("typ") != "zricenina" else 0
    
    cursor.execute("""
        INSERT INTO pamatky (id, nazev, typ, kraj, popis, lat, lng, dostupny_auto, dostupny_kocárek)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        hrad.get("id"),
        hrad.get("nazev"),
        hrad.get("typ"),
        hrad.get("kraj"),
        hrad.get("popis"),
        hrad.get("lat"),
        hrad.get("lng"),
        dostupny_auto,
        dostupny_kocárek
    ))
    if (i + 1) % 50 == 0:
        print(f"   Vloženo {i + 1}/{len(hrady)}")

conn.commit()
conn.close()

print("✅ JSON a databáze opraveny!")
print("\nSample - nové kraje:")
with open("hrady_data.json", "r", encoding="utf-8") as f:
    sample = json.load(f)[:10]
    for s in sample:
        print(f"  {s['nazev']}: {s['kraj']}")
