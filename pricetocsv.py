from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import keepaAPI
import csv
import time


class NoItems(Exception):
    pass


class PriceToCSV:
    def __init__(self, keepa_accesskey):
        self.keepa_accesskey = keepa_accesskey
        self.keepa_api = keepaAPI.API(keepa_accesskey)
        gecko_options = Options()
        gecko_options.headless = True
        self.web_driver = webdriver.Firefox(options=gecko_options, executable_path='./geckodriver')

    def get_asin(self, product_name):
        # 아마존 검색어로 asin을 알아옴. 서버 상황에 따라 최대 3회 검색 시도.
        # 성공시 해당 물건의 asin 리턴, 실패시 에러 (서버에 접속 불가하거나, 물건이 없는 경우)
        searched_items = None

        for i in range(3):
            # 최대 3회 아마존에서 검색을 시도 한다.
            self.web_driver.get('https://www.amazon.com/s?k=' + product_name)
            html = self.web_driver.page_source
            souped_html = BeautifulSoup(html, 'html.parser')
            searched_items = souped_html.find_all('div', {'data-index': '0'}, limit=1)

            if searched_items:
                break

            time.sleep(0.3)  # 실패시 잠시 쉼

        if not searched_items:
            raise NoItems

        first_item = searched_items[0]
        product_asin = first_item.attrs['data-asin']

        return product_asin

    def save_csv(self, product_name, price_zip_list):
        with open('{0}.csv'.format(product_name), 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar=',', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['date', 'price'])
            for row in price_zip_list:
                csv_writer.writerow(row)

    def get_prices(self, product_asin):
        products = self.keepa_api.ProductQuery(product_asin)
        product = products[0]
        price_zip_list = list(zip(product['data']['NEW_time'], product['data']['NEW']))
        return price_zip_list

    def keyword_generator(self, brand, model, args):
        if args:
            words = [brand, model] + list(args)
        else:
            words = [brand, model]
        keyword = ' '.join(words)
        return keyword

    def make_price_csv(self, brand, model, *args):
        try:
            keyword = self.keyword_generator(brand, model, args)
            product_asin = self.get_asin(keyword)
            price_zip_list = self.get_prices(product_asin)
            self.save_csv(keyword, price_zip_list)
            print('Done!')
        except NoItems:
            print('There are no items for the keyword or Search server seems having some problems.')


# make_csv = PriceToCSV('2b63aol2vkmetj1lb1vii4a2knk9c07ik7bru5ihlctovg5t71mrtg3g48jfffd3')
# make_csv.make_price_csv('amd', 'yd270xbgafbox')
