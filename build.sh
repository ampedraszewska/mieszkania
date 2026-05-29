#!/usr/bin/env bash
# Buduje zaszyfrowaną stronę index.html z danych ofert.
#
# Użycie:
#   ./build.sh "HASŁO"            # przebuduj z istniejących danych (data/listings.json)
#   ./build.sh "HASŁO" --scrape   # najpierw pobierz świeże dane z otodom, potem zbuduj
#
# Po zbudowaniu: git add -A && git commit -m "update" && git push
set -euo pipefail
cd "$(dirname "$0")"

PASSWORD="${1:-}"
if [ -z "$PASSWORD" ]; then
  echo "Podaj hasło: ./build.sh \"HASŁO\" [--scrape]" >&2
  exit 1
fi

if [ "${2:-}" = "--scrape" ]; then
  echo "==> Pobieram świeże dane z otodom..."
  python3 scrape.py
fi

echo "==> Generuję dashboard..."
python3 build.py

echo "==> Szyfruję do index.html..."
node encrypt_gate.js dashboard.html "$PASSWORD" index.html

echo "==> Gotowe. Publiczne repo zawiera tylko zaszyfrowany index.html."
echo "    Wyślij: git add -A && git commit -m 'update' && git push"
