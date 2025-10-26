# scripts/update_metals_playwright_week.py
# Usage: python3 scripts/update_metals_playwright_week.py data/metals_week.html
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import sys, time, os, re

URL = "https://www.metalsmine.com/calendar?week=this"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36"
)

def wait_for_calendar(page, max_wait=90):
    """
    Чекаємо, поки зникне Cloudflare і з’явиться таблиця календаря.
    Працюємо через кілька етапів із резервними перевірками.
    """
    start = time.time()
    # 1) початкове завантаження
    page.wait_for_load_state("domcontentloaded", timeout=60000)
    # якщо видно челендж — чекаємо, поки сторінка “розблокується”
    # робимо кілька спроб перевіряти наявність таблиці
    while True:
        html = page.content()
        if "Verifying you are human" not in html and "challenge-platform" not in html:
            try:
                page.wait_for_selector("table.calendar__table", state="attached", timeout=3000)
                return  # таблиця є в DOM
            except PWTimeout:
                pass
        # якщо минув ліміт — валимося
        if time.time() - start > max_wait:
            raise RuntimeError("calendar table did not appear in time (likely stuck on Cloudflare challenge)")
        # іноді допомагає додатковий await networkidle
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except PWTimeout:
            pass
        time.sleep(1)

def save_table_content(page, out_file: str):
    """
    Дістаємо саме <table class="calendar__table"> і зберігаємо outerHTML.
    """
    el = page.query_selector("table.calendar__table")
    if not el:
        raise RuntimeError("calendar table not found on the page")
    html = page.evaluate("el => el.outerHTML", el)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)

def main(out_path: str):
    print(f"[playwright-week] goto {URL}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent=UA,
            java_script_enabled=True,
            viewport={"width": 1280, "height": 2000},
        )
        # Виставимо невеличкий кеш, щоб не дертись кожної секунди (не обов'язково)
        page = context.new_page()
        page.set_default_timeout(60000)
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        # інколи Cloudflare перезавантажує URL — просто чекаємо
        wait_for_calendar(page, max_wait=90)

        save_table_content(page, out_path)

        browser.close()
    print(f"[playwright-week] saved → {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: update_metals_playwright_week.py <OUTPUT_HTML>")
        sys.exit(1)
    main(sys.argv[1])