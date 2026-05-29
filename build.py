#!/usr/bin/env python3
"""Buduje dashboard.html + mieszkania-google-maps.csv z data/listings.json.
Ręczne poprawki (ulice, daty dostępności) trzymaj w OVERRIDES.
"""
import json, html, datetime, os, math, csv

HERE = os.path.dirname(os.path.abspath(__file__))

# Google Sheet „Tracker mieszkań" — wspólny, edytowalny przez Ciebie i chłopaka.
# Dashboard pobiera z niego dane na żywo (kolumny: Status / Kto dzwonił / Co ustalono / Notatki),
# kluczem jest ID oferty (kolumna A). Edycja: przycisk „Otwórz tracker" na stronie.
SHEET_ID = "1r08LM2oHW6xgIKpFORNJTpUb_8mEKkQW7-cW4nXR8fg"
SHEET_TAB = "Tracker"

# Oferty wycofane / niedostępne — pomijane przy budowaniu (klucz = fragment ID z URL).
EXCLUDE = {"ID4BjUK"}  # Nowogrodzka — oferta niedostępna (zdjęta 2026-05-29)

# Ręczne nadpisania pól, których otodom nie podaje poprawnie / strukturalnie.
# Klucz = fragment ID z URL oferty.
OVERRIDES = {
    "ID4Aw2S": {"ulica": "Plac Trzech Krzyży"},
    "ID4BjUK": {"ulica": "Nowogrodzka"},
    "ID4BnQH": {"dostepne_od": "2026-05-18"},
    "ID4BgZm": {"ulica": "Górskiego 2"},  # Restaura Górskiego — otodom nie podaje ulicy
    "ID4uDHh": {"ulica": "Górskiego 1"},  # druga oferta na Górskiego (Restaura)
}

# Centralne stacje metra Warszawy (M1 + M2): nazwa -> (lat, lng)
STATIONS = {
    "Rondo Daszyńskiego (M2)": (52.2296, 20.9844),
    "Rondo ONZ (M2)": (52.2329, 20.9967),
    "Świętokrzyska (M1/M2)": (52.2353, 21.0083),
    "Nowy Świat-Uniwersytet (M2)": (52.2384, 21.0166),
    "Centrum Nauki Kopernik (M2)": (52.2415, 21.0286),
    "Stadion Narodowy (M2)": (52.2487, 21.0440),
    "Politechnika (M1)": (52.2192, 21.0116),
    "Centrum (M1)": (52.2299, 21.0107),
    "Ratusz Arsenał (M1)": (52.2452, 20.9996),
    "Dworzec Gdański (M1)": (52.2585, 20.9844),
    "Plac Wilsona (M1)": (52.2697, 20.9889),
}

def num(s):
    return int("".join(ch for ch in (s or "") if ch in "0123456789") or 0)

def zl(n):
    return f"{n:,}".replace(",", " ") + " zł"

def hav(a, b, c, e):
    R = 6371000
    p1, p2 = math.radians(a), math.radians(c)
    dp = math.radians(c - a); dl = math.radians(e - b)
    x = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

def nearest_metro(lat, lng):
    best, bd = None, 1e18
    for name, (slat, slng) in STATIONS.items():
        d = hav(lat, lng, slat, slng)
        if d < bd:
            best, bd = name, d
    return best, round(bd)

def load():
    data = json.load(open(os.path.join(HERE, "data", "listings.json")))
    data = [r for r in data if not any(x in r.get("url", "") for x in EXCLUDE)]
    for r in data:
        for frag, ov in OVERRIDES.items():
            if frag in r.get("url", ""):
                r.update(ov)
        # Bez prefiksu „ul." — ani w dashboard, ani w trackerze
        u = (r.get("ulica") or "").strip()
        for pref in ("ul. ", "ul.", "Ul. ", "Ul."):
            if u.startswith(pref):
                u = u[len(pref):].strip()
                break
        r["ulica"] = u
        if r.get("lat") and r.get("lng"):
            r["metro"], r["metro_m"] = nearest_metro(r["lat"], r["lng"])
        else:
            r["metro"], r["metro_m"] = "", None
    data.sort(key=lambda r: num(r.get("cena")) + num(r.get("czynsz_adm")))
    return data

def build():
    data = load()
    rows, points = [], []
    for i, r in enumerate(data, 1):
        ulica = html.escape(r.get("ulica") or "")
        dz = html.escape(r.get("dzielnica") or "")
        addr = f'{ulica}<span class="dz">{(" · " + dz) if dz else ""}</span>'
        metraz = html.escape(r.get("metraz") or "")
        pokoje = html.escape(r.get("pokoje") or "")
        sauna = r.get("sauna") or "nie"
        parking = r.get("parking") or "nie"
        total_n = num(r.get("cena")) + num(r.get("czynsz_adm"))
        czynsz = html.escape(r.get("czynsz_adm") or "")
        kaucja = html.escape(r.get("kaucja") or "")
        odkiedy = html.escape(r.get("dostepne_od") or "")
        metro = html.escape(r.get("metro") or "")
        metro_m = r.get("metro_m")
        metro_cell = (f'{metro}<span class="brk">~{metro_m} m</span>' if metro else "—")
        pos = html.escape(r.get("posrednik") or "")
        tel = html.escape(r.get("telefon") or "")
        telhref = (r.get("telefon") or "").split(",")[0].strip().replace(" ", "")
        url = html.escape(r.get("url") or "")

        def chip(v):
            cls = "yes" if v == "tak" else "no"
            return f'<span class="chip {cls}">{"✓ tak" if v=="tak" else "—"}</span>'

        tel_cell = f'<a href="tel:{telhref}" class="tel">{tel}</a>' if telhref else "—"
        rid = "ID" + (r.get("url") or "").split("-ID")[-1]
        rows.append(f"""    <tr data-id="{html.escape(rid)}">
      <td class="idx">{i}</td>
      <td class="addr"><a href="{url}" target="_blank">{addr}</a></td>
      <td class="num" data-sort="{num(metraz)}">{metraz}</td>
      <td class="num">{pokoje}</td>
      <td class="ctr">{chip(sauna)}</td>
      <td class="ctr">{chip(parking)}</td>
      <td class="num price" data-sort="{total_n}">{zl(total_n)}<span class="brk">w tym czynsz: {czynsz or '—'}</span></td>
      <td class="num small">{kaucja}</td>
      <td class="small metro" data-sort="{metro_m if metro_m is not None else 999999}">{metro_cell}</td>
      <td class="small">{odkiedy}</td>
      <td>{pos}</td>
      <td class="tel-cell">{tel_cell}</td>
      <td class="trk-status small"></td>
      <td class="trk-notes small"></td>
    </tr>""")
        if r.get("lat") and r.get("lng"):
            points.append({"n": i, "lat": r["lat"], "lng": r["lng"],
                "ulica": r.get("ulica") or "", "dz": r.get("dzielnica") or "",
                "total": total_n, "metraz": r.get("metraz") or "", "sauna": sauna,
                "tel": r.get("telefon") or "", "url": r.get("url") or "",
                "metro": r.get("metro") or "", "metro_m": r.get("metro_m")})

    # CSV do Google My Maps
    with open(os.path.join(HERE, "mieszkania-google-maps.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nazwa","lat","lng","metraz","cena_calkowita","sauna","metro","telefon","link"])
        for p in points:
            nazwa = f'{p["n"]}. {p["ulica"]}' + (f' ({p["dz"]})' if p["dz"] else "")
            mt = f'{p["metro"]} (~{p["metro_m"]} m)' if p["metro"] else ""
            w.writerow([nazwa,p["lat"],p["lng"],p["metraz"],f'{p["total"]} zł',p["sauna"],mt,p["tel"],p["url"]])

    today = datetime.date.today().isoformat()
    n = len(data)
    n_sauna = sum(1 for r in data if r.get("sauna") == "tak")
    doc = TEMPLATE.format(today=today, n=n, n_sauna=n_sauna,
                          rows=chr(10).join(rows), points=json.dumps(points, ensure_ascii=False),
                          sheet_id=SHEET_ID, sheet_tab=SHEET_TAB)
    open(os.path.join(HERE, "dashboard.html"), "w", encoding="utf-8").write(doc)
    print(f"Wrote dashboard.html + mieszkania-google-maps.csv ({n} ofert)")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Mieszkania na wynajem — Warszawa</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  :root {{ --bg:#0f1115; --card:#181b22; --line:#262b35; --txt:#e8ebf0; --mut:#8b93a3; --accent:#7aa2ff; --green:#3ecf8e; --price:#ffd166; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--txt); font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif; padding:32px 20px; }}
  h1 {{ font-size:22px; margin:0 0 4px; }}
  .sub {{ color:var(--mut); margin:0 0 20px; font-size:13px; }}
  .wrap {{ max-width:1280px; margin:0 auto; }}
  .stats {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:18px; }}
  .stat {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:10px 14px; }}
  .stat b {{ font-size:18px; }} .stat span {{ color:var(--mut); font-size:12px; display:block; }}
  table {{ width:100%; border-collapse:collapse; background:var(--card); border:1px solid var(--line); border-radius:12px; overflow:hidden; }}
  th, td {{ padding:11px 12px; text-align:left; border-bottom:1px solid var(--line); vertical-align:middle; }}
  th {{ background:#1d212a; color:var(--mut); font-size:11px; text-transform:uppercase; letter-spacing:.04em; cursor:pointer; user-select:none; white-space:nowrap; }}
  th:hover {{ color:var(--txt); }}
  tr:last-child td {{ border-bottom:none; }}
  tbody tr:hover {{ background:#1e232d; }}
  .idx {{ color:var(--mut); width:28px; }}
  .addr a {{ color:var(--accent); text-decoration:none; font-weight:600; }}
  .addr a:hover {{ text-decoration:underline; }}
  .dz {{ color:var(--mut); font-weight:400; font-size:12px; }}
  .num {{ text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }}
  .ctr {{ text-align:center; }}
  .price {{ color:var(--price); font-weight:700; }}
  .price .brk, .metro .brk {{ display:block; color:var(--mut); font-weight:400; font-size:11px; }}
  .small {{ font-size:12px; color:var(--mut); }}
  .chip {{ display:inline-block; padding:2px 8px; border-radius:20px; font-size:12px; font-weight:600; }}
  .chip.yes {{ background:rgba(62,207,142,.15); color:var(--green); }}
  .chip.no {{ background:transparent; color:var(--mut); }}
  .tel {{ color:var(--txt); text-decoration:none; font-variant-numeric:tabular-nums; }}
  .tel:hover {{ color:var(--accent); }}
  .tel-cell {{ white-space:nowrap; }}
  #map {{ height:460px; border-radius:12px; border:1px solid var(--line); margin-bottom:18px; }}
  .pin {{ background:var(--accent); color:#0f1115; font-weight:700; border:2px solid #fff; border-radius:50%; width:26px; height:26px; line-height:22px; text-align:center; font-size:13px; box-shadow:0 1px 4px rgba(0,0,0,.5); }}
  .pin.sauna {{ background:var(--green); }}
  .leaflet-popup-content {{ font:13px/1.45 -apple-system,sans-serif; }}
  .leaflet-popup-content a {{ color:#1a56db; }}
  footer {{ color:var(--mut); font-size:12px; margin-top:16px; }}
  .trk-btn {{ background:var(--accent); color:#0f1115; text-decoration:none; font-weight:700; font-size:13px; padding:10px 16px; border-radius:10px; display:inline-flex; align-items:center; }}
  .trk-btn:hover {{ filter:brightness(1.08); }}
  .trk-status {{ font-weight:600; }}
  .trk-status .s {{ display:inline-block; padding:2px 8px; border-radius:20px; font-size:12px; }}
  .trk-status .s-hot {{ background:rgba(62,207,142,.15); color:var(--green); }}
  .trk-status .s-wait {{ background:rgba(255,209,102,.15); color:var(--price); }}
  .trk-status .s-no {{ background:rgba(139,147,163,.15); color:var(--mut); }}
  .trk-notes b {{ color:var(--txt); font-weight:600; }}
  .trk-notes .lbl {{ color:var(--mut); }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Mieszkania na wynajem — Warszawa</h1>
  <p class="sub">Śródmieście / Powiśle · zebrane z otodom.pl · {today} · kliknij nagłówek kolumny, żeby sortować · zielona pinezka = sauna w budynku</p>
  <div class="stats">
    <div class="stat"><b>{n}</b><span>ofert</span></div>
    <div class="stat"><b>{n_sauna}</b><span>z sauną w budynku</span></div>
    <div class="stat"><b>{n}</b><span>z parkingiem/garażem</span></div>
    <a class="trk-btn" href="https://docs.google.com/spreadsheets/d/{sheet_id}/edit" target="_blank">✏️ Otwórz tracker — kto dzwonił / co ustalono</a>
  </div>
  <p class="sub" id="trk-info">Status i notatki ładują się na żywo z arkusza. Edytujcie w trackerze — po odświeżeniu strony zmiany pojawią się tutaj.</p>
  <div id="map"></div>
  <table id="t">
    <thead>
      <tr>
        <th>#</th>
        <th>Ulica</th>
        <th class="num">Metraż</th>
        <th class="num">Pok.</th>
        <th class="ctr">Sauna</th>
        <th class="ctr">Parking</th>
        <th class="num">Cena całkowita/mc</th>
        <th class="num">Kaucja</th>
        <th>Najbliższa stacja metra</th>
        <th>Dostępne od</th>
        <th>Pośrednik</th>
        <th>Telefon</th>
        <th>Status</th>
        <th>Kto dzwonił / ustalenia / notatki</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>
  <footer>Cena całkowita = najem + czynsz administracyjny. Sauna = sauna w budynku/ofercie. Odległość do metra liczona w linii prostej. Dane mogą się zmieniać — zweryfikuj u pośrednika.</footer>
</div>
<script>
  const POINTS = {points};
  const map = L.map('map').setView([52.231, 21.018], 14);
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
    attribution: '&copy; OpenStreetMap, &copy; CARTO', maxZoom: 19
  }}).addTo(map);
  const bounds = [];
  POINTS.forEach(p => {{
    const icon = L.divIcon({{ className:'', html:'<div class="pin'+(p.sauna==='tak'?' sauna':'')+'">'+p.n+'</div>',
      iconSize:[26,26], iconAnchor:[13,13], popupAnchor:[0,-14] }});
    const pop = '<b>'+p.n+'. '+p.ulica+'</b>'+(p.dz?' · '+p.dz:'')+
      '<br>'+p.metraz+' · <b>'+p.total.toLocaleString('pl-PL')+' zł/mc</b>'+
      (p.sauna==='tak'?'<br>🧖 sauna w budynku':'')+
      (p.metro?'<br>🚇 '+p.metro+' (~'+p.metro_m+' m)':'')+
      '<br>📞 '+p.tel+'<br><a href="'+p.url+'" target="_blank">otwórz ofertę →</a>';
    L.marker([p.lat,p.lng], {{icon}}).addTo(map).bindPopup(pop);
    bounds.push([p.lat,p.lng]);
  }});
  if (bounds.length) map.fitBounds(bounds, {{padding:[40,40]}});
  const table = document.getElementById('t');
  table.querySelectorAll('th').forEach((th, idx) => {{
    let asc = true;
    th.addEventListener('click', () => {{
      const tb = table.tBodies[0];
      const rows = Array.from(tb.rows);
      rows.sort((a,b) => {{
        const ca=a.cells[idx], cb=b.cells[idx];
        const va=ca.dataset.sort!==undefined?parseFloat(ca.dataset.sort):ca.innerText.trim().toLowerCase();
        const vb=cb.dataset.sort!==undefined?parseFloat(cb.dataset.sort):cb.innerText.trim().toLowerCase();
        if(va<vb) return asc?-1:1; if(va>vb) return asc?1:-1; return 0;
      }});
      asc=!asc; rows.forEach(r => tb.appendChild(r));
    }});
  }});

  // --- Tracker na żywo z Google Sheet (gviz, CORS-friendly) ---
  const SHEET_ID = "{sheet_id}";
  const SHEET_TAB = "{sheet_tab}";
  const GVIZ = 'https://docs.google.com/spreadsheets/d/'+SHEET_ID+'/gviz/tq?tqx=out:json&sheet='+encodeURIComponent(SHEET_TAB);
  function esc(s){{ const d=document.createElement('div'); d.textContent=(s==null?'':String(s)); return d.innerHTML; }}
  function statusChip(s){{
    const t=(s||'').toString().trim(); if(!t) return '';
    const low=t.toLowerCase(); let cls='s-wait';
    if(/(umów|umow|zainteres|tak|ok|super|świetn|do obejrz|ogląd|oferta|wizyt)/.test(low)) cls='s-hot';
    else if(/(odpada|nie |wynaj|zaj[eę]t|rezygn|brak|odrzu)/.test(low)) cls='s-no';
    return '<span class="s '+cls+'">'+esc(t)+'</span>';
  }}
  fetch(GVIZ).then(r=>r.text()).then(txt=>{{
    const m=txt.match(/setResponse\((.*)\)/s); if(!m) return;
    const d=JSON.parse(m[1]); const rows=d.table.rows; const byId={{}};
    for(let i=1;i<rows.length;i++){{
      const c=rows[i].c; if(!c) continue;
      const id=(c[0]&&c[0].v)?String(c[0].v).trim():''; if(!id) continue;
      byId[id]={{status:c[10]&&c[10].v, viewing:c[11]&&c[11].v, kto:c[12]&&c[12].v, ust:c[13]&&c[13].v, not:c[14]&&c[14].v}};
    }}
    document.querySelectorAll('#t tbody tr').forEach(tr=>{{
      const v=byId[tr.dataset.id]; if(!v) return;
      const st=tr.querySelector('.trk-status'); if(st) st.innerHTML=statusChip(v.status);
      const parts=[];
      if(v.kto) parts.push('<span class="lbl">kto:</span> '+esc(v.kto));
      if(v.viewing) parts.push('<span class="lbl">viewing:</span> '+esc(v.viewing));
      if(v.ust) parts.push('<span class="lbl">ustalenia:</span> '+esc(v.ust));
      if(v.not) parts.push('<span class="lbl">notatki:</span> '+esc(v.not));
      const nt=tr.querySelector('.trk-notes'); if(nt) nt.innerHTML=parts.join('<br>');
    }});
  }}).catch(e=>{{
    const el=document.getElementById('trk-info'); if(el) el.textContent='Nie udało się pobrać trackera (sprawdź połączenie).';
  }});
</script>
</body>
</html>"""

if __name__ == "__main__":
    build()
