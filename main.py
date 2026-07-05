import sqlite3
from fastapi import FastAPI, Request, Form, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import hashlib
import secrets
from datetime import datetime, timedelta
import json

app = FastAPI(title="Lovci Hradů API")
templates = Jinja2Templates(directory="templates")

# Funkce pro připojení k databázi
def get_db_connection():
    conn = sqlite3.connect("databaze.db")
    conn.row_factory = sqlite3.Row
    return conn

# Hash hesla
def hash_heslo(heslo):
    return hashlib.sha256(heslo.encode()).hexdigest()

# Generuj token
def generate_token():
    return secrets.token_urlsafe(32)

# Ověř session
def get_current_user(session_token: str = Cookie(None)):
    if not session_token:
        return None
    
    conn = get_db_connection()
    user = conn.execute("""
        SELECT u.* FROM uzivatele u
        JOIN sessions s ON u.id = s.uzivatel_id
        WHERE s.token = ? AND (s.vyprsela IS NULL OR s.vyprsela > datetime('now'))
    """, (session_token,)).fetchone()
    conn.close()
    
    return user

# 1. HLAVNÍ STRÁNKA
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, session_token: str = Cookie(None)):
    current_user = get_current_user(session_token)
    
    conn = get_db_connection()
    hrady_z_db = conn.execute("SELECT * FROM pamatky ORDER BY nazev ASC").fetchall()
    
    # Pokud je přihlášený, načti jeho navštívené památky
    navstivene = []
    if current_user:
        navstivene_rows = conn.execute("""
            SELECT pamatka_id FROM navstivene_pamatky WHERE uzivatel_id = ?
        """, (current_user['id'],)).fetchall()
        navstivene = [row['pamatka_id'] for row in navstivene_rows]
    
    conn.close()
    
    return templates.TemplateResponse(request, "index.html", {
        "hrady": hrady_z_db,
        "current_user": current_user,
        "navstivene": json.dumps(navstivene)
    })

# 2. REGISTRACE
@app.post("/registruj")
async def registruj(
    jmeno: str = Form(...),
    email: str = Form(...),
    heslo: str = Form(...),
    heslo2: str = Form(...)
):
    if heslo != heslo2:
        return {"error": "Hesla se neshodují"}
    
    if len(heslo) < 6:
        return {"error": "Heslo musí mít alespoň 6 znaků"}
    
    conn = get_db_connection()
    
    # Zkontroluj jestli email už existuje
    existing = conn.execute("SELECT id FROM uzivatele WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return {"error": "Tento email je již registrován"}
    
    # Vytvoř uživatele
    heslo_hashed = hash_heslo(heslo)
    conn.execute("""
        INSERT INTO uzivatele (email, heslo, jmeno)
        VALUES (?, ?, ?)
    """, (email, heslo_hashed, jmeno))
    conn.commit()
    conn.close()
    
    return RedirectResponse(url="/prihlaseni", status_code=303)

# 3. PŘIHLÁŠENÍ
@app.get("/prihlaseni", response_class=HTMLResponse)
async def get_prihlaseni(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@app.post("/prihlaseni")
async def prihlaseni(
    email: str = Form(...),
    heslo: str = Form(...)
):
    conn = get_db_connection()
    heslo_hashed = hash_heslo(heslo)
    
    user = conn.execute("""
        SELECT * FROM uzivatele WHERE email = ? AND heslo = ?
    """, (email, heslo_hashed)).fetchone()
    
    if not user:
        conn.close()
        return {"error": "Špatný email nebo heslo"}
    
    # Vytvoř session token
    token = generate_token()
    vyprsela = datetime.now() + timedelta(days=30)
    
    conn.execute("""
        INSERT INTO sessions (uzivatel_id, token, vyprsela)
        VALUES (?, ?, ?)
    """, (user['id'], token, vyprsela))
    conn.commit()
    conn.close()
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("session_token", token, max_age=30*24*60*60, httponly=True)
    return response

# 4. ODHLÁŠENÍ
@app.get("/odhlasit")
async def odhlasit(session_token: str = Cookie(None)):
    if session_token:
        conn = get_db_connection()
        conn.execute("DELETE FROM sessions WHERE token = ?", (session_token,))
        conn.commit()
        conn.close()
    
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_token")
    return response

# 5. FORMULÁŘ - Ukládá nová místa do databáze
@app.post("/pridat")
async def pridat_misto(
    nazev: str = Form(...),
    kraj: str = Form(...),
    typ: str = Form(...),
    popis: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    foto_url: str = Form(None),
    dostupny_auto: bool = Form(False),
    dostupny_kocárek: bool = Form(False)
):
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

# 6. API - Vrací data s filtrováním
@app.get("/api/hrady")
async def get_hrady_api(
    kraj: str = None,
    dostupny_auto: bool = None,
    dostupny_kocárek: bool = None
):
    conn = get_db_connection()
    
    query = "SELECT * FROM pamatky WHERE 1=1"
    params = []
    
    if kraj and kraj != "Česko":
        query += " AND kraj = ?"
        params.append(kraj)
    
    if dostupny_auto:
        query += " AND dostupny_auto = 1"
    
    if dostupny_kocárek:
        query += " AND dostupny_kocárek = 1"
    
    query += " ORDER BY nazev ASC"
    
    hrady_z_db = conn.execute(query, params).fetchall()
    conn.close()
    
    return [{key: row[key] for key in row.keys()} for row in hrady_z_db]

# 7. API - Označit místo jako navštívené
@app.post("/api/navstivit/{pamatka_id}")
async def navstivit(pamatka_id: int, session_token: str = Cookie(None)):
    user = get_current_user(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Není přihlášený")
    
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO navstivene_pamatky (uzivatel_id, pamatka_id)
            VALUES (?, ?)
        """, (user['id'], pamatka_id))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Už je označeno
    finally:
        conn.close()
    
    return {"success": True}

# 8. API - Odebrat značku návštěvy
@app.post("/api/nenavstivit/{pamatka_id}")
async def nenavstivit(pamatka_id: int, session_token: str = Cookie(None)):
    user = get_current_user(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Není přihlášený")
    
    conn = get_db_connection()
    conn.execute("""
        DELETE FROM navstivene_pamatky WHERE uzivatel_id = ? AND pamatka_id = ?
    """, (user['id'], pamatka_id))
    conn.commit()
    conn.close()
    
    return {"success": True}

# 9. API - Vrátí navštívené památky uživatele
@app.get("/api/moje-navstivene")
async def get_moje_navstivene(session_token: str = Cookie(None)):
    user = get_current_user(session_token)
    if not user:
        return []
    
    conn = get_db_connection()
    navstivene = conn.execute("""
        SELECT pamatka_id FROM navstivene_pamatky WHERE uzivatel_id = ?
    """, (user['id'],)).fetchall()
    conn.close()
    
    return [row['pamatka_id'] for row in navstivene]
