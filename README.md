# Mieszkania na wynajem — Warszawa

Prywatny dashboard ofert najmu (Śródmieście / Powiśle), zaszyfrowany hasłem i hostowany na GitHub Pages.

**Strona:** https://AMP_USER.github.io/mieszkania/ (wpisz hasło, żeby zobaczyć)

## Jak to działa (prywatność)

Strona jest szyfrowana **po stronie klienta** (AES-GCM + PBKDF2). Do publicznego repo trafia
tylko zaszyfrowany `index.html` — bez hasła to bezużyteczny szyfrogram. Surowe dane z numerami
pośredników (`data/listings.json`, `dashboard.html`, CSV) są w `.gitignore` i **nigdy** nie idą do repo.

## Dodanie / aktualizacja ofert

1. Dopisz URL oferty otodom do listy `URLS` w [`scrape.py`](scrape.py)
2. Przebuduj i zaszyfruj:
   ```bash
   ./build.sh "HASŁO" --scrape     # pobiera świeże dane + buduje
   ```
   albo bez ponownego pobierania (gdy zmieniasz tylko wygląd / poprawki):
   ```bash
   ./build.sh "HASŁO"
   ```
3. Wyślij:
   ```bash
   git add -A && git commit -m "nowa oferta: ..." && git push
   ```
   GitHub Pages zaktualizuje stronę w ~1 minutę.

## Ręczne poprawki

Otodom czasem nie podaje ulicy albo daty dostępności w polach strukturalnych.
Takie poprawki trzymaj w słowniku `OVERRIDES` w [`build.py`](build.py) (klucz = fragment ID z URL).

## Wymagania lokalne

- Python 3 (scraper + generator, bez zależności poza standardową biblioteką)
- Node.js (szyfrowanie — `encrypt_gate.js`, używa wbudowanego Web Crypto)
- `curl`
