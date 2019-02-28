from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import keepa
import csv
import time

class NoFile(Exception):
    pass


class NoItems(Exception):
    pass


class PriceToCSV:
    def __init__(self, keepa_accesskey):
        self.keepa_accesskey = keepa_accesskey
        self.keepa_api = keepa.Keepa(keepa_accesskey)
        self.saved_file_name = 'price_info'
        self.is_file_created = False
        gecko_options = Options()
        gecko_options.headless = True
        self.web_driver = webdriver.Firefox(options=gecko_options, executable_path='./geckodriver')

    def get_asin(self, product_name):
        # 아마존 검색어로 asin을 알아옴. 서버 상황에 따라 최대 3회 검색 시도.
        # 성공시 해당 물건의 asin 리턴, 실패시 에러 (서버에 접속 불가하거나, 물건이 없는 경우)
        searched_items = None

        for i in range(5):
            # 최대 5회 아마존에서 검색을 시도 한다.
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

    def create_csv(self, file_name=None):
        if file_name:
            self.saved_file_name = file_name
        with open('{0}.csv'.format(self.saved_file_name), 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar=',', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['brand', 'model', 'note', 'date', 'price'])
        self.is_file_created = True

    def write_csv(self, brand, model, note, price_zip_list):
        with open('{0}.csv'.format(self.saved_file_name), 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar=',', quoting=csv.QUOTE_MINIMAL)
            for row in price_zip_list:
                csv_writer.writerow([brand, model, note] + list(row))

    def get_prices(self, product_asin):
        products = self.keepa_api.query(product_asin)
        product = products[0]
        price_zip_list = list(zip(product['data']['NEW_time'], product['data']['NEW']))
        return price_zip_list

    def save_csv(self, brand, model, *args):
        try:
            if not self.is_file_created:
                raise NoFile
            if args:
                note = ' '.join(list(args))
            else:
                note = ''
            product_asin = self.get_asin(' '.join([brand, model, note]))
            price_zip_list = self.get_prices(product_asin)
            self.write_csv(brand, model, note, price_zip_list)
            print('Done!')
        except NoItems:
            print('There are no items for the keyword or Search server seems having some problems.')
        except NoFile:
            print('please, make file first.')
'''
make_csv = PriceToCSV('2b63aol2vkmetj1lb1vii4a2knk9c07ik7bru5ihlctovg5t71mrtg3g48jfffd3')
make_csv.create_csv()
make_csv.save_csv('amd', 'yd270xbgafbox')
make_csv.save_csv('apple', 'iphoneX')
변경점
쓰기 전에 make_csv.create_csv 필요 (필요에 따라 파일 네임을 인자로 줄수있고, 기본값도있음)
make_price_csv의 이름이 save_csv로 변경
'''