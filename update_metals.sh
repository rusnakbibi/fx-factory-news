#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${BASE_DIR}/metals_today.html"
TMP="${BASE_DIR}/.metals_tmp.html"
URL="https://www.metalsmine.com/calendar?day=today"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "Fetch → ${URL}"

# Спроба 1: curl із “браузерними” заголовками
curl -sS -L --compressed "${URL}" \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Referer: https://www.metalsmine.com/' \
  --output "${TMP}" || { log "ERROR: curl failed"; exit 1; }

BYTES=$(wc -c < "${TMP}" | tr -d ' ')
# Евристики: якщо мало байтів або на сторінці є ознаки Cloudflare/challenge — вважаємо невдачею
if [[ "${BYTES}" -lt 50000 ]] || grep -qiE 'cf-mitigated|Just a moment|cloudflare|challenge' "${TMP}"; then
  log "Curl looks blocked (size=${BYTES}). Trying Playwright fallback…"
  # Спроба 2: Playwright (реальний браузер)
  python3 "${BASE_DIR}/update_metals_playwright.py" "${OUT}" || {
    log "ERROR: Playwright fallback failed too."
    rm -f "${TMP}"
    exit 1
  }
  log "Saved via Playwright → ${OUT}"
  rm -f "${TMP}"
  exit 0
fi

# Якщо curl дав нормальний HTML — витягнемо саме таблицю (щоб файл був «чистим» для парсера)
python3 - <<'PY' "${TMP}" "${OUT}"
import sys, re, pathlib
from bs4 import BeautifulSoup

src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
soup = BeautifulSoup(src, "html.parser")
tbl = soup.select_one("table.calendar__table")
if not tbl:
    # fallback: запишемо як є
    pathlib.Path(sys.argv[2]).write_text(src, encoding="utf-8")
else:
    html = str(tbl)
    pathlib.Path(sys.argv[2]).write_text(html, encoding="utf-8")
PY

rm -f "${TMP}"
log "Saved via curl → ${OUT}"