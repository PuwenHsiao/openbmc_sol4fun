
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


class WebScraper:
    def __init__(self):
        self.url = None
        self._text = None

    @property
    def source(self):
        return self.url

    @source.setter
    def source(self, url):
        self.url = url
        self._text = None

    @property
    def text(self):
        if self._text:
            return self._text
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://24h.pchome.com.tw/store/DCBR0R?style=2')
            self._text = page.content()
            browser.close()
        return self._text

    def show(self):
        soup = BeautifulSoup(self.text, 'lxml')
        product_container = soup.find('div', {'id': 'ProdListContainer'})
        product_list = product_container.find_all('dl', {'class': 'col3f'})
        print(f'Found {len(product_list)} products')
        for product in product_list:
            print(product)
            print('----------------------------------------')


if __name__ == '__main__':
    scraper = WebScraper()
    scraper.source = 'https://24h.pchome.com.tw/store/DCBR0R?style=2'
    scraper.show()
