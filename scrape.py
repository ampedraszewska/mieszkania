#!/usr/bin/env python3
"""Pobiera oferty z otodom.pl i zapisuje surowe dane do data/listings.json.
Dodawanie nowej oferty: dopisz URL do listy URLS poniżej i uruchom `python3 scrape.py`.
"""
import re, json, subprocess, sys, os

URLS = [
    "https://www.otodom.pl/pl/oferta/wysoki-standard-pierwszy-najem-klimatyzacja-parking-od-zaraz-ID4BvkC",
    "https://www.otodom.pl/pl/oferta/apartament-80m2-w-centrum-restaura-gorskiego-ID4uDHh",
    "https://www.otodom.pl/pl/oferta/nowoczesne-3-pok-63m2-srodmiescie-garaz-ID4AV60",
    "https://www.otodom.pl/pl/oferta/100m2-2-sypialnie-kamienica-ul-konopczynskiego-ID4zo6q",
    "https://www.otodom.pl/pl/oferta/3-pok-krakowskie-przedmiescie-miejsce-park-ID4AcvN",
    "https://www.otodom.pl/pl/oferta/3brd-apartment-powisle-70-m2-for-rent-ID4BeIB",
    "https://www.otodom.pl/pl/oferta/apartament-w-stylu-glamour-na-powislu-ID4Aofu",
    "https://www.otodom.pl/pl/oferta/quiet-city-center-location-comfortable-apartment-with-balcony-ID4Bfpd",
    "https://www.otodom.pl/pl/oferta/exclusive-3-rooms-garage-plac-trzech-krzyzy-ID4Aw2S",
    "https://www.otodom.pl/pl/oferta/apartament-z-balkonem-widok-na-park-ID4BhYZ",
    "https://www.otodom.pl/pl/oferta/komfortowe-3-wysokie-pokoje-w-centrum-parking-ID4BtXd",
    "https://www.otodom.pl/pl/oferta/centrum-klimatyzacja-balkon-parking-w-cenie-ID4BjUK",
    "https://www.otodom.pl/pl/oferta/mennica-residence-3-pokoje-taras-premium-ID4BaKg",
    "https://www.otodom.pl/pl/oferta/apartament-w-rezydencji-rozana-ID4BnQH",
    "https://www.otodom.pl/pl/oferta/78m2-3-pokoje-klimatyzacja-restaura-gorskiego-ID4BgZm",
]

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def fetch(url):
    out = subprocess.run(
        ["curl", "-sS", "-A", UA, "-H", "Accept-Language: pl-PL,pl;q=0.9", url],
        capture_output=True, text=True, timeout=60)
    return out.stdout

def char(chars, key):
    for c in chars:
        if c.get("key") == key:
            return c
    return None

def main():
    results = []
    for url in URLS:
        rec = {"url": url}
        try:
            html = fetch(url)
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
            if not m:
                rec["error"] = "no NEXT_DATA"; results.append(rec); continue
            ad = json.loads(m.group(1))["props"]["pageProps"]["ad"]
            chars = ad.get("characteristics", [])
            addr = ad.get("location", {}).get("address", {}) or {}
            street = (addr.get("street") or {})
            st_name = street.get("name") or ""
            st_no = street.get("number") or ""
            street_full = (st_name + (" " + st_no if st_no else "")).strip()
            rec["ulica"] = street_full if street_full else "(brak ulicy)"
            rec["dzielnica"] = (addr.get("district") or {}).get("name") or ""
            coords = ad.get("location", {}).get("coordinates") or {}
            rec["lat"] = coords.get("latitude"); rec["lng"] = coords.get("longitude")
            for key, field in [("m","metraz"),("rooms_num","pokoje"),("price","cena"),
                               ("rent","czynsz_adm"),("deposit","kaucja"),("free_from","dostepne_od")]:
                c = char(chars, key); rec[field] = c["localizedValue"] if c else ""
            cd = ad.get("contactDetails") or {}
            rec["posrednik"] = (cd.get("name") or "").strip()
            rec["telefon"] = ", ".join(cd.get("phones") or [])
            blob = json.dumps(ad, ensure_ascii=False).lower()
            tgt = ad.get("target", {})
            extras = [e.lower() for e in (tgt.get("Extras_types") or [])]
            rec["sauna"] = "tak" if "sauna" in blob else "nie"
            rec["parking"] = "tak" if ("garage" in extras or "parking" in extras or "garaż" in blob or "miejsce postojowe" in blob) else "nie"
        except Exception as e:
            rec["error"] = str(e)
        results.append(rec)
        print(f"OK {rec.get('ulica','?')[:30]:30} | {rec.get('metraz',''):8} | {rec.get('cena',''):12} | sauna={rec.get('sauna','')} tel={rec.get('telefon','')}", file=sys.stderr)

    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "data", "listings.json")
    json.dump(results, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"\nWrote {out} ({len(results)} ofert)", file=sys.stderr)

if __name__ == "__main__":
    main()
