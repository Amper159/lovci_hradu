import sqlite3

conn = sqlite3.connect("databaze.db")
cursor = conn.cursor()

try:
    # Přidáme do tabulky nový sloupec pro URL adresu obrázku
    cursor.execute("ALTER TABLE pamatky ADD COLUMN foto_url TEXT")
    print("✅ Sloupec 'foto_url' byl úspěšně přidán do tabulky!")
except sqlite3.OperationalError:
    print("ℹ️ Sloupec 'foto_url' už v databázi existuje.")

# Jako výchozí fotku nastavíme hezkou neutrální siluetu hradu z Unsplash,
# aby tam nebylo prázdné místo, dokud nestáhneme reálné fotky.
vychozi_foto = "https://images.unsplash.com/photo-1500835556837-99ac94a94552?w=500&q=80"

cursor.execute("UPDATE pamatky SET foto_url = ?", (vychozi_foto,))
conn.commit()
conn.close()

print("✅ Všechny stávající památky dostaly výchozí obrázek.")
