from pathlib import Path

import requests
from bs4 import BeautifulSoup

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
        self._text = requests.get(self.url).text
        return self._text

    def show(self):
        soup = BeautifulSoup(self.text, 'lxml')
        Path('cache/01.html').write_text(soup.prettify(), encoding='utf-8')
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

