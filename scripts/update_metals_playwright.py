# scripts/update_metals_playwright.py
import sys
import os
import time
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright, Error as PWError

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/metals_today.html")
URL = "https://www.metalsmine.com/calendar?day=today"

def _log(msg: str):
    print(msg, flush=True)

def _ensure_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def _try_launch_chromium(pw):
    # На Render зазвичай треба --no-sandbox
    return pw.chromium.launch(headless=True, args=["--no-sandbox"])

def _install_browsers():
    _log("[playwright] installing chromium at runtime…")
    env = os.environ.copy()
    # гарантуємо цільову директорію
    env.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/render/.cache/ms-playwright")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True, env=env)

def main():
    _ensure_dir(OUT)
    _log(f"[playwright] target file: {OUT}")

    with sync_playwright() as pw:
        # 1-а спроба: запуск як є
        try:
            browser = _try_launch_chromium(pw)
        except PWError as e:
            if "Executable doesn't exist" in str(e):
                # авто-рекавері: довантажуємо браузер і пробуємо ще раз
                _install_browsers()
                browser = _try_launch_chromium(pw)
            else:
                raise

        try:
            ctx = browser.new_context(user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/127.0.0.0 Safari/537.36"
            ))
            page = ctx.new_page()
            _log(f"[playwright] goto {URL}")
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            # трошки зачекаємо, якщо там щось дорендерюється
            time.sleep(2)

            # Прагнемо витягнути лише таблицю, але якщо немає — збережемо всю сторінку
            html = page.content()
            from bs4 import BeautifulSoup  # є в requirements.txt
            soup = BeautifulSoup(html, "html.parser")
            table = soup.select_one("table.calendar__table")
            html_out = str(table) if table else html

            OUT.write_text(html_out, encoding="utf-8")
            _log(f"[playwright] saved → {OUT} ({OUT.stat().st_size} bytes)")
        finally:
            browser.close()

if __name__ == "__main__":
    main()