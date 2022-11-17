
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from pathlib import Path
from bs4.element import NavigableString


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
        filename = self.url
        for char in ['/', ':', '?', '&', '=', '.']:
            filename = filename.replace(char, '_')
        cache = Path(f'cache/{filename}.html')
        cache.parent.mkdir(parents=True, exist_ok=True)
        if cache.exists():
            self._text = cache.read_text(encoding='utf-8')
            return self._text
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://24h.pchome.com.tw/store/DCBR0R?style=2')
            self._text = page.content()
            cache.write_text(self._text, encoding='utf-8')
            browser.close()
        return self._text

    def show(self):
        soup = BeautifulSoup(self.text, 'lxml')
        product_container = soup.find('div', {'id': 'ProdListContainer'})
        product_list = product_container.find_all('dl', {'class': 'col3f'})
        print(f'Found {len(product_list)} products')
        product_data = []
        for product in product_list:
            reader = {}
            image = product.select('img')[0]
            nick = [x for x in product.select('.nick > a')][0]
            nick = [x for x in nick.children if isinstance(x, NavigableString)][0]
            price_normal = product.select('.price > .value')[0]
            price_prime = product.select('.price > .value')[1]
            reader['image'] = image['src']
            reader['name'] = nick.encode('utf-8')
            reader['price'] = {
                'normal': price_normal.text,
                'prime': price_prime.text,
            }
            product_data.append(reader)
        print(f'{"image_url":<64} {"ebook_reader_name":<72} {"normal_price":<16} {"prime_price":<16}')
        for data in product_data:
            image = data['image']
            name = data['name']
            price_normal = data['price']['normal']
            price_prime = data['price']['prime']
            diff = 72 - int((len(name) - len(name.decode('utf-8'))) / 2)
            print(f'{image:<64} {name.decode("utf-8"):<{diff}} {price_normal:<16} {price_prime:<16}')


if __name__ == '__main__':
    scraper = WebScraper()
    scraper.source = 'https://24h.pchome.com.tw/store/DCBR0R?style=2'
    scraper.show()
