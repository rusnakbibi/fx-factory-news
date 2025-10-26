#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${METALS_WEEK_HTML:-${BASE_DIR%/*}/data/metals_week.html}"  # /data/... на Render або локально ./data/...
TMP="${BASE_DIR}/.metals_week_tmp.html"
URL="https://www.metalsmine.com/calendar?week=this"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# ✅ створимо каталог, куди писатимемо HTML
mkdir -p "$(dirname "$OUT")"

log "Fetch (WEEK) → ${URL}"

# 1) curl
curl -sS -L --compressed "${URL}" \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Referer: https://www.metalsmine.com/' \
  --output "${TMP}" || { log "ERROR: curl (week) failed"; exit 1; }

BYTES=$(wc -c < "${TMP}" | tr -d ' ')

if [[ "${BYTES}" -lt 50000 ]] || grep -qiE 'cf-mitigated|Just a moment|cloudflare|challenge' "${TMP}"; then
  log "Curl (week) looks blocked (size=${BYTES}). Trying Playwright fallback…"
  python3 "${BASE_DIR}/update_metals_playwright_week.py" "${OUT}" || {
    log "ERROR: Playwright (week) fallback failed."
    rm -f "${TMP}"
    exit 1
  }
  rm -f "${TMP}"
  exit 0
fi

# 2) якщо curl дав хороший HTML — візьмемо лише саму таблицю
python3 - <<'PY' "${TMP}" "${OUT}"
import sys, pathlib
from bs4 import BeautifulSoup
src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
soup = BeautifulSoup(src, "html.parser")
tbl = soup.select_one("table.calendar__table")
html = str(tbl) if tbl else src
pathlib.Path(sys.argv[2]).write_text(html, encoding="utf-8")
PY

rm -f "${TMP}"
log "Saved (week) via curl → ${OUT}"