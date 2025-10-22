# update_metals_playwright.py
import sys, pathlib, asyncio
from bs4 import BeautifulSoup

URL = "https://www.metalsmine.com/calendar?day=today"

async def main(out_path: str):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/127.0.0.0 Safari/537.36)")
        )
        page = await ctx.new_page()
        # Перейти на сторінку і дочекатися основної таблиці
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        # Іноді потрібен невеликий wait, поки докинуться елементи
        await page.wait_for_selector("table.calendar__table", timeout=60000)
        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    tbl = soup.select_one("table.calendar__table")
    out = pathlib.Path(out_path)
    out.write_text(str(tbl if tbl else soup), encoding="utf-8")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "metals_today.html"
    asyncio.run(main(out))