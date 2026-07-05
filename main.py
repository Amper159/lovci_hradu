import sqlite3
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Lovci Hradů API")
templates = Jinja2Templates(directory="templates")

# Funkce pro připojení k databázi
def get_db_connection():
    conn = sqlite3.connect("databaze.db")
    conn.row_factory = sqlite3.Row
    return conn

# 1. HLAVNÍ STRÁNKA - Načítá data živě z SQL databáze
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    conn = get_db_connection()
    # Vytáhneme všechny památky seřazené podle abecedy
    hrady_z_db = conn.execute("SELECT * FROM pamatky ORDER BY nazev ASC").fetchall()
    conn.close()
    
    # NOVÝ ZÁPIS PRO MODERNÍ FASTAPI: request jde jako první, pak název šablony, pak data
    return templates.TemplateResponse(request, "index.html", {"hrady": hrady_z_db})

# 2. FORMULÁŘ - Ukládá nová místa od lidí TRVALE do databáze
@app.post("/pridat")
async def pridat_misto(
    nazev: str = Form(...),
    kraj: str = Form(...),
    typ: str = Form(...),
    popis: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    foto_url: str = Form(None),  # Nový nepovinný parametr
    dostupny_auto: bool = Form(False),
    dostupny_kocárek: bool = Form(False)
):
    # Pokud uživatel nevyplní fotku, dáme tam výchozí siluetu hradu
    if not foto_url:
        foto_url = "https://images.unsplash.com/photo-1500835556837-99ac94a94552?w=500&q=80"
        
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO pamatky (nazev, typ, kraj, popis, lat, lng, foto_url, dostupny_auto, dostupny_kocárek)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nazev, typ, kraj, popis, lat, lng, foto_url, dostupny_auto, dostupny_kocárek))
    conn.commit()
    conn.close()
    
    return RedirectResponse(url="/", status_code=303)

# 3. API - Vrací čistá data z DB s filtrováním
@app.get("/api/hrady")
async def get_hrady_api(
    kraj: str = None,
    dostupny_auto: bool = None,
    dostupny_kocárek: bool = None
):
    conn = get_db_connection()
    
    query = "SELECT * FROM pamatky WHERE 1=1"
    params = []
    
    # Filtrování podle kraju
    if kraj and kraj != "Česko":
        query += " AND kraj = ?"
        params.append(kraj)
    
    # Filtrování podle dostupnosti autem
    if dostupny_auto:
        query += " AND dostupny_auto = 1"
    
    # Filtrování podle dostupnosti s kočárkem
    if dostupny_kocárek:
        query += " AND dostupny_kocárek = 1"
    
    query += " ORDER BY nazev ASC"
    
    hrady_z_db = conn.execute(query, params).fetchall()
    conn.close()
    
    # BEZPEČNÝ ZÁPIS: Ručně vytáhneme klíče a hodnoty z každého SQL řádku
    return [{key: row[key] for key in row.keys()} for row in hrady_z_db]
