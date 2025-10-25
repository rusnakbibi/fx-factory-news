import sys, time, pathlib
from playwright.sync_api import sync_playwright

URL = "https://www.metalsmine.com/calendar?day=today"

def main(out_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/127.0.0.0 Safari/537.36"
        ))
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        # Трохи зачекати, якщо таблиця підвантажується
        for _ in range(10):
            if page.locator("table.calendar__table").count() > 0:
                break
            time.sleep(0.5)

        html = ""
        if page.locator("table.calendar__table").count() > 0:
            html = page.locator("table.calendar__table").first.inner_html()
            html = f"<table class=\"calendar__table\">{html}</table>"
        else:
            html = page.content()

        pathlib.Path(out_path).write_text(html, encoding="utf-8")
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m scripts.update_metals_playwright /data/metals_today.html")
        sys.exit(2)
    main(sys.argv[1])