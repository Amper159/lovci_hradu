import sqlite3
import requests
import time

print("⏳ Spouštím vyhledávání reálných fotek na Wikipedii pro 183 památek...")

conn = sqlite3.connect("databaze.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Vytáhneme všechny památky z DB
pamatky = cursor.execute("SELECT id, nazev FROM pamatky").fetchall()

headers = {
    "User-Agent": "LovciHraduBot/2.0 (kontakt: tvuj-email-vymysleny@seznam.cz)"
}

uspesne_aktualizovano = 0

for pamatka in pamatky:
    pamatka_id = pamatka["id"]
    nazev = pamatka["nazev"]
    
    # API endpoint pro vyhledávání na české Wikipedii podle názvu hradu
    wiki_url = "https://cs.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(nazev)
    
    try:
        response = requests.get(wiki_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # Podíváme se, zda článek obsahuje hlavní obrázek (originalimage)
            if "originalimage" in data and "source" in data["originalimage"]:
                foto_url = data["originalimage"]["source"]
                
                # Uložíme reálnou URL fotky do naší databáze
                cursor.execute("UPDATE pamatky SET foto_url = ? WHERE id = ?", (foto_url, pamatka_id))
                print(f"📸 Nalezena fotka pro: {nazev}")
                uspesne_aktualizovano += 1
            else:
                print(f"ℹ️ Pro {nazev} článek existuje, ale nemá hlavní fotku.")
        else:
            # Pokud přesný název selže, zkusíme najít aspoň čisté klíčové slovo bez "Zámek" nebo "Hrad"
            cisty_nazev = nazev.replace("Hrad ", "").replace("Zámek ", "").replace("Zřícenina hradu ", "")
            wiki_url_retry = "https://cs.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(cisty_nazev)
            response_retry = requests.get(wiki_url_retry, headers=headers, timeout=5)
            
            if response_retry.status_code == 200:
                data_retry = response_retry.json()
                if "originalimage" in data_retry and "source" in data_retry["originalimage"]:
                    foto_url = data_retry["originalimage"]["source"]
                    cursor.execute("UPDATE pamatky SET foto_url = ? WHERE id = ?", (foto_url, pamatka_id))
                    print(f"📸 Nalezena fotka (na 2. pokus) pro: {nazev}")
                    uspesne_aktualizovano += 1
                    
        # Drobná pauza, ať nepřetížíme Wikipedii
        time.sleep(0.1)
        
    except Exception as e:
        print(f"❌ Chyba při komunikaci u {nazev}: {e}")

# Potvrdíme změny do souboru databaze.db
conn.commit()
conn.close()

print(f"\n✅ Hotovo! Úspěšně naimportováno {uspesne_aktualizovano} reálných fotografií z Wikipedie.")
