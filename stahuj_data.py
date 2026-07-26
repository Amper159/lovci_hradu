import json
import re
import requests


def analyzuj_dostupnost(text):
    """Prohledá textový popis památky a podle klíčových slov určí,

    zda je místo dostupné autem a/nebo vhodné pro kočárek.
    """
    if not text:
        return {'auto': 0, 'kocarek': 0}

    text_lower = str(text).lower()

    # Klíčová slova pro vyhledávání
    auto_kw = [
        'parkoviště',
        'parkování',
        'autem',
        'parkovat',
        'příjezd',
        'silnice',
        'příjezdová',
    ]
    kocarek_kw = [
        'kočárek',
        'kočárky',
        'bezbariérový',
        'bezbariérové',
        'pro kočárky',
        's kočárkem',
        'zpevněná',
        'asfaltová',
    ]

    dostupnost_auto = 1 if any(kw in text_lower for kw in auto_kw) else 0
    dostupnost_kocarek = 1 if any(kw in text_lower for kw in kocarek_kw) else 0

    return {'auto': dostupnost_auto, 'kocarek': dostupnost_kocarek}


def stahuj_data_o_hradech():
    print('1. Odesílám dotaz na Wikidata SPARQL API...')

    # SPARQL dotaz na české hrady a zámky s GPS a fotkou
    sparql_query = """
    SELECT ?item ?itemLabel ?lat ?lon ?image ?krajLabel ?description WHERE {
      ?item wdt:P31/wdt:P279* wd:Q23413;        # Hrady/zámky
            wdt:P17 wd:Q213;                  # V České republice
            wdt:P625 ?coord.                  # Mají GPS souřadnice
      
      OPTIONAL { ?item wdt:P18 ?image. }      # Obrázek
      OPTIONAL { ?item wdt:P131 ?kraj. }     # Správní oblast / Kraj
      OPTIONAL { ?item schema:description ?description. FILTER(LANG(?description) = "cs") }

      # Získání zeměpisné šířky a délky
      BIND(geof:latitude(?coord) AS ?lat)
      BIND(geof:longitude(?coord) AS ?lon)

      SERVICE wikibase:label { bd:serviceParam wikibase:language "cs". }
    }
    LIMIT 300
    """

    url = 'https://query.wikidata.org/sparql'
    headers = {
        'User-Agent': 'LovciHraduBot/1.0 (moje_emailova_adresa@example.com)'
    }

    try:
        response = requests.get(
            url,
            params={'query': sparql_query, 'format': 'json'},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        raw_data = response.json()['results']['bindings']
        print(f'-> Načteno {len(raw_data)} záznamů z API.')
    except Exception as e:
        print(f'❌ Chyba při stahování dat: {e}')
        return

    print('2. Zpracovávám a analyzuji data (auto, kočárek, souřadnice)...')

    vystupni_data = []
    vyuzita_id = set()

    for item in raw_data:
        nazev = item.get('itemLabel', {}).get('value', 'Neznámá památka')
        
        # Přeskočíme duplicity podle názvu
        if nazev in vyuzita_id:
            continue
        vyuzita_id.add(nazev)

        lat = float(item.get('lat', {}).get('value', 0))
        lon = float(item.get('lon', {}).get('value', 0))
        foto = item.get('image', {}).get('value', '')
        kraj = item.get('krajLabel', {}).get('value', 'Neznámý kraj')
        popis = item.get('description', {}).get('value', '')

        # Analýza dostupnosti autem a kočárkem z popisu/názvu
        cely_text = f'{nazev} {popis}'
        dostupnost = analyzuj_dostupnost(cely_text)

        vystupni_data.append({
            'nazev': nazev,
            'kraj': kraj,
            'lat': lat,
            'lon': lon,
            'foto': foto,
            'auto': dostupnost['auto'],
            'kocarek': dostupnost['kocarek'],
        })

    print(f'3. Ukládám {len(vystupni_data)} vyčištěných památek do JSONu...')

    with open('hrady_data.json', 'w', encoding='utf-8') as f:
        json.dump(vystupni_data, f, ensure_ascii=False, indent=4)

    print('✅ Hotovo! Soubor hrady_data.json byl úspěšně aktualizován.')


if __name__ == '__main__':
    stahuj_data_o_hradech()