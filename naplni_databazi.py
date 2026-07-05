import json
import sqlite3

print("1. Načítám JSON...")
with open("hrady_data.json", "r", encoding="utf-8") as f:
    hrady = json.load(f)
print(f"   Načteno {len(hrady)} památek")

print("2. Připojuji se k databázi...")
conn = sqlite3.connect("databaze.db")
cursor = conn.cursor()

print("3. Mažu staré data...")
cursor.execute("DELETE FROM pamatky")
print(f"   Smazáno")

print("4. Vkládám nová data...")
for i, hrad in enumerate(hrady):
    try:
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
    except Exception as e:
        print(f"   CHYBA u памятке {hrad.get('nazev')}: {e}")

print("5. Ukládám databázi...")
conn.commit()
conn.close()

print(f"✅ Naplněno {len(hrady)} památek do databáze!")
