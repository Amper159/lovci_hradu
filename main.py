from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Lovci Hradů API")

# Nastavení šablon pro HTML
templates = Jinja2Templates(directory="templates")

# Testovací databáze hradů a zámků (v budoucnu nahradíš skutečnou SQL databází)
HRADY_DATA = [
    {
        "id": 1,
        "nazev": "Hrad Karlštejn",
        "popis": "Monumentální gotický hrad založený Karlem IV. Ideální cíl na víkendový vlakový výlet z Prahy.",
        "kraj": "Středočeský",
        "typ": "hrad",
        "tagy": ["Top místo", "Historie"],
        "lat": 49.9391,
        "lng": 14.1883
    },
    {
        "id": 2,
        "nazev": "Zřícenina hradu Trosky",
        "popis": "Ikonická dominanta Českého ráje se dvěma věžemi jménem Panna a Baba. Úžasný výhled do okolí.",
        "kraj": "Liberecký",
        "typ": "zricenina",
        "tagy": ["V lese", "Výhled"],
        "lat": 50.5163,
        "lng": 15.2307
    },
    {
        "id": 3,
        "nazev": "Zámek Lednice",
        "popis": "Pohádkový novogotický zámek obklopený jedním z největších zámeckých parků v Evropě.",
        "kraj": "Jihomoravský",
        "typ": "zamek",
        "tagy": ["Pro kočárky", "Zahrada"],
        "lat": 48.8001,
        "lng": 16.8041
    }
]

# 1. Hlavní routa pro webový prohlížeč (Zobrazí web)
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
   return templates.TemplateResponse(request, "index.html", {"hrady": HRADY_DATA})

# 2. API Endpoit pro mobilní aplikaci (Vrací čistá data v JSON)
@app.get("/api/hrady")
async def get_hrady_api():
    return HRADY_DATA