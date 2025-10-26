#!/usr/bin/env bash
set -euo pipefail

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# ---- де зберігати HTML ----
# локально зручно ./data/metals_today.html, на Render став METALS_TODAY_HTML=/data/metals_today.html
OUT="${METALS_TODAY_HTML:-/data/metals_today.html}"
TMP="$(mktemp -t metals_today.XXXXXX.html)"
URL="https://www.metalsmine.com/calendar?day=today"

# знайдемо інтерпретатор Python
PY_BIN="${PY_BIN:-$(command -v python3 || true)}"
if [[ -z "${PY_BIN}" ]]; then
  PY_BIN="$(command -v python || true)"
fi
if [[ -z "${PY_BIN}" ]]; then
  log "ERROR: Python not found. Install Python 3 (e.g. 'brew install python' or use a venv)."
  exit 1
fi

mkdir -p "$(dirname "$OUT")"

log "Fetch → ${URL}"

# Спроба 1: curl (імітуємо браузер)
curl -sS -L --compressed "${URL}" \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Referer: https://www.metalsmine.com/' \
  --output "${TMP}" || { log "ERROR: curl failed"; exit 1; }

BYTES=$(wc -c < "${TMP}" | tr -d ' ')
if [[ "${BYTES}" -lt 50000 ]] || grep -qiE 'cf-mitigated|Just a moment|cloudflare|challenge' "${TMP}"; then
  log "Curl looks blocked (size=${BYTES}). Trying Playwright fallback…"
  python3 scripts/update_metals_playwright.py "${OUT}" || {
    log "ERROR: Playwright fallback failed too."
    rm -f "${TMP}"
    exit 1
  }
  log "Saved via Playwright → ${OUT}"
  rm -f "${TMP}"
  exit 0
fi

# Якщо curl дав нормальний HTML — витягнемо саму таблицю
"${PY_BIN}" - "${TMP}" "${OUT}" <<'PY'
import sys, pathlib
from bs4 import BeautifulSoup

src_path, out_path = sys.argv[1], sys.argv[2]
src = pathlib.Path(src_path).read_text(encoding="utf-8", errors="ignore")
soup = BeautifulSoup(src, "html.parser")
tbl = soup.select_one("table.calendar__table")
if not tbl:
    # якщо таблицю не знайшли — збережемо як є (парсер у тебе вміє з повної сторінки теж)
    pathlib.Path(out_path).write_text(src, encoding="utf-8")
else:
    pathlib.Path(out_path).write_text(str(tbl), encoding="utf-8")
PY

rm -f "${TMP}"
log "Saved via curl → ${OUT}"