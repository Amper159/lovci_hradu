import sqlite3
import os

conn = sqlite3.connect("databaze.db")
cursor = conn.cursor()

print("1. Vytvářím tabulku 'uzivatele'...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS uzivatele (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        heslo TEXT,
        google_id TEXT UNIQUE,
        jmeno TEXT,
        profilni_foto TEXT,
        vytvoren_dne TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

print("2. Vytvářím tabulku 'navstivene_pamatky'...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS navstivene_pamatky (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uzivatel_id INTEGER NOT NULL,
        pamatka_id INTEGER NOT NULL,
        navstiveno_dne TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (uzivatel_id) REFERENCES uzivatele(id),
        FOREIGN KEY (pamatka_id) REFERENCES pamatky(id),
        UNIQUE(uzivatel_id, pamatka_id)
    )
""")

print("3. Vytvářím tabulku 'sessions'...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uzivatel_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        vytvorena TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        vyprsela TIMESTAMP,
        FOREIGN KEY (uzivatel_id) REFERENCES uzivatele(id)
    )
""")

conn.commit()
conn.close()

print("✅ Databázové tabulky vytvořeny!")
