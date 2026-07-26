import json
import sqlite3

DATABASE = 'databaze.db'
JSON_FILE = 'hrady_data.json'


def naplni_databazi():
    print('1. Načítám JSON...')
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f'   Načteno {len(data)} památek.')

    print('2. Připojuji se k databázi...')
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # ZDE PŘIDÁME SMAZÁNÍ STARÉ TABULKY:
    cursor.execute('DROP TABLE IF EXISTS pamatky')

    # Nyní se tabulka vytvoří úplně znovu se všemi novými sloupci
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pamatky (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nazev TEXT,
            kraj TEXT,
            lat REAL,
            lon REAL,
            foto TEXT,
            auto INTEGER DEFAULT 0,
            kocarek INTEGER DEFAULT 0
        )
    ''')

    print('3. Mažu stará data...')
    cursor.execute('DELETE FROM pamatky')
    print('   Smazáno.')

    print('4. Vkládám nová data vč. dostupnosti (auto, kočárek)...')
    pocet = 0
    for item in data:
        cursor.execute(
            '''
            INSERT INTO pamatky (nazev, kraj, lat, lon, foto, auto, kocarek)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
            (
                item.get('nazev'),
                item.get('kraj'),
                item.get('lat'),
                item.get('lon'),
                item.get('foto'),
                item.get('auto', 0),
                item.get('kocarek', 0),
            ),
        )
        pocet += 1
        if pocet % 50 == 0:
            print(f'   Vloženo {pocet}/{len(data)}')

    conn.commit()
    conn.close()
    print(f'✅ Naplněno {pocet} památek do databáze!')


if __name__ == '__main__':
    naplni_databazi()