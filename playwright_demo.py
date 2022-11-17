from pathlib import Path

from playwright.sync_api import sync_playwright

if __name__ == '__main__':
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://24h.pchome.com.tw/store/DCBR0R?style=2')
        print(page.title())
        Path('test.html').write_text(page.content(), encoding='utf-8')
        page.screenshot(path='example.png', full_page=True)
        browser.close()
