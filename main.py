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
# 2. FORMULÁŘ - Ukládá nová místa od lidí TRVALE do databáze
@app.post("/pridat")
async def pridat_misto(
    nazev: str = Form(...),
    kraj: str = Form(...),
    typ: str = Form(...),
    popis: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    foto_url: str = Form(None)  # Nový nepovinný parametr
):
    # Pokud uživatel nevyplní fotku, dáme tam výchozí siluetu hradu
    if not foto_url:
        foto_url = "https://images.unsplash.com/photo-1500835556837-99ac94a94552?w=500&q=80"
        
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO pamatky (nazev, typ, kraj, popis, lat, lng, foto_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nazev, typ, kraj, popis, lat, lng, foto_url))
    conn.commit()
    conn.close()
    
    return RedirectResponse(url="/", status_code=303)
# 3. API - Vrací čistá data z DB
# 3. API - Vrací čistá data z DB
@app.get("/api/hrady")
async def get_hrady_api():
    conn = get_db_connection()
    hrady_z_db = conn.execute("SELECT * FROM pamatky").fetchall()
    conn.close()
    
    # BEZPEČNÝ ZÁPIS: Ručně vytáhneme klíče a hodnoty z každého SQL řádku
    return [{key: row[key] for key in row.keys()} for row in hrady_z_db]