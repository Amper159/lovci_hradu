import json
import sqlite3

# 1. Načtení dat ze staženého JSON souboru
try:
    with open("hrady_data.json", "r", encoding="utf-8") as f:
        hrady = json.load(f)
except FileNotFoundError:
    print("❌ Chyba: Soubor 'hrady_data.json' nebyl nalezen v této složce!")
    exit()

# 2. Připojení k SQLite databázi
conn = sqlite3.connect("databaze.db")
cursor = conn.cursor()

# 3. Vytvoření tabulky pro památky
cursor.execute("""
CREATE TABLE IF NOT EXISTS pamatky (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nazev TEXT NOT NULL,
    typ TEXT NOT NULL,
    kraj TEXT,
    popis TEXT,
    lat REAL NOT NULL,
    lng REAL NOT NULL
)
""")

# 4. Vyčištění starých dat
cursor.execute("DELETE FROM pamatky")

# 5. Vložení všech památek do tabulky
for hrad in hrady:
    cursor.execute("""
    INSERT INTO pamatky (nazev, typ, kraj, popis, lat, lng)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (hrad["nazev"], hrad["typ"], hrad["kraj"], hrad["popis"], hrad["lat"], hrad["lng"]))

conn.commit()
conn.close()

print("✅ Výborně! Soubor 'databaze.db' byl vytvořen a naplněn.")
