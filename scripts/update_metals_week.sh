#!/usr/bin/env bash
set -euo pipefail

# до кореня репо
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
OUT="${METALS_WEEK_HTML:-/data/metals_week.html}"
TMP="${BASE_DIR}/.metals_week_tmp.html"
URL="https://www.metalsmine.com/calendar?week=this"

log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

mkdir -p "${BASE_DIR}/data"

log "Fetch (WEEK) → ${URL}"

# 1) Спочатку пробуємо curl
curl -sS -L --compressed "${URL}" \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Referer: https://www.metalsmine.com/' \
  -o "${TMP}" || { log "ERROR: curl (week) failed"; exit 1; }

BYTES=$(wc -c < "${TMP}" | tr -d ' ')
if [[ "${BYTES}" -lt 50000 ]] || grep -qiE 'cf-mitigated|Just a moment|cloudflare|challenge' "${TMP}"; then
  log "Curl (week) looks blocked (size=${BYTES}). Trying Playwright fallback…"
  # 2) Фолбек: Playwright — ВАЖЛИВО: передаємо шлях вихідного файлу!
  python3 "${BASE_DIR}/scripts/update_metals_playwright_week.py" "${OUT}" || {
    log "ERROR: Playwright (week) fallback failed."
    rm -f "${TMP}"
    exit 1
  }
  rm -f "${TMP}"
  exit 0
fi

# 3) Якщо curl спрацював — дістаємо тільки таблицю
python3 - <<'PY' "${TMP}" "${OUT}"
import sys, pathlib
from bs4 import BeautifulSoup

src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
soup = BeautifulSoup(src, "html.parser")
tbl = soup.select_one("table.calendar__table")
pathlib.Path(sys.argv[2]).write_text(str(tbl) if tbl else src, encoding="utf-8")
PY

rm -f "${TMP}"
log "Saved (WEEK) via curl → ${OUT}"