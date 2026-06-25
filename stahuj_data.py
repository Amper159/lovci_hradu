import json
import requests

print("⏳ Připojuji se k OpenStreetMap a stahuji české hrady a zámky...")

overpass_url = "https://overpass-api.de/api/interpreter"
overpass_query = """
[out:json][timeout:30];
area["ISO3166-1"="CZ"]->.searchArea;
(
  node["historic"="castle"](area.searchArea);
  way["historic"="castle"](area.searchArea);
);
out center;
"""

# Hlavička, která se představí serveru, aby nás neblokoval jako anonymního robota
headers = {
    "User-Agent": "LovciHraduBot/1.0 (kontakt: tvuj-email-klidne-vymysleny@seznam.cz)"
}

try:
    # Přidali jsme parametr headers=headers
    response = requests.post(overpass_url, data={"data": overpass_query}, headers=headers, timeout=40)
    
    if response.status_code != 200:
        print(f"❌ Server vrátil chybu s kódem {response.status_code}. Zkus to za chvíli znovu.")
        if response.status_code == 406:
            print("💡 Tip: Server stále odmítá požadavek. Ověř správnost hlavičky User-Agent.")
        exit()
        
    data = response.json()
    seznam_pamatek = []
    counter = 1

    for element in data.get("elements", []):
        lat = element.get("lat") or element.get("center", {}).get("lat")
        lng = element.get("lon") or element.get("center", {}).get("lng")
        
        tags = element.get("tags", {})
        nazev = tags.get("name")
        
        if nazev and lat and lng:
            castle_type = tags.get("castle_type", "")
            
            if "ruins" in tags or castle_type == "ruins" or "zřícenina" in nazev.lower():
                typ = "zricenina"
            elif "zámek" in nazev.lower() or castle_type == "manor":
                typ = "zamek"
            else:
                typ = "hrad"
                
            pamatka = {
                "id": counter,
                "nazev": nazev,
                "typ": typ,
                "kraj": tags.get("addr:region", "Česko"),
                "popis": f"Historický {typ} {nazev}. Data importována z OpenStreetMap.",
                "lat": round(lat, 5),
                "lng": round(lng, 5)
            }
            seznam_pamatek.append(pamatka)
            counter += 1

    with open("hrady_data.json", "w", encoding="utf-8") as f:
        json.dump(seznam_pamatek, f, ensure_ascii=False, indent=4)

    print(f"✅ Hotovo! Vytvořen soubor 'hrady_data.json'.")
    print(f"📊 Celkem úspěšně staženo a zpracováno {len(seznam_pamatek)} památek z celé ČR!")

except json.JSONDecodeError:
    print("❌ Server vrátil neplatný formát dat (pravděpodobně je přetížený). Spusť skript znovu za 10 vteřin.")
except Exception as e:
    print(f"❌ Došlo k chybě: {e}")