import keepa
import csv
import re
from google import google

'''
딱히 기존 코드 부분은 변경하지 않고, model , brand가 없을 때만 
 save_cvs('', '', '제목') 형태로 호출하면 됩니다.
'''
'''
이번 버전에서 변경된 점:
뉴에그와 아마존의 상품정보가 100% 일치 하지 않을 수도 있으므로 ASIN 정보를 추가적으로 기입함.
google 검색을 통해 아마존을 검색함 (검색 정확도 향상)
아마존 주소체계:
https://www.amazon.com/Dell-Inspiron-7000-Touchscreen-Quad-Core/dp/B01NCHZTMY
https://www.amazon.com/키워드/dp/ASIN

brand 나 model이 없는 경우 빈 스트링 입력후, 제목 입력 바람
(즉, save_cvs('', '', '제목') 형태로 호출
신규 의존성 : pip install git+https://github.com/abenassi/Google-Search-API
'''
'''
조금 의논이 필요한 사항,
brand하고 model이 없는 경우,
brand의 경우 대부분 맨 앞에 있는 단어인데,
이것을 문자열 처리로 저장해서 cvs에 저장할 데이터로 취급 할 것인가?
'''

class NoFile(Exception):
    pass


class NoKeepaData(Exception):
    pass

class NoASIN(Exception):
    pass


class PriceToCSV:
    def __init__(self, keepa_accesskey):
        self.keepa_accesskey = keepa_accesskey
        self.keepa_api = keepa.Keepa(keepa_accesskey)
        self.saved_file_name = 'price_info'
        self.is_file_created = False

    def get_asin(self, product_name):
        # 구글을 통해 아마존 검색 후, asin을 구할 수 있으면 넘겨 주고,
        # 그렇지 않은 경우 다음 검색결과에서 asin을 찾아보고 넘겨준다. 최대 5번 시도.
        searched_items = google.search('site:www.amazon.com ' + product_name, 1)

        for item in searched_items:
            if item.link:
                searched_re = re.search('https://www.amazon.com/.+?/dp/(?P<ASIN>\w{10})', item.link)
                if searched_re:
                    product_asin = searched_re.group('ASIN')
                    return product_asin

        raise NoASIN

    def create_csv(self, file_name=None):
        if file_name:
            self.saved_file_name = file_name
        with open('data/price/price_info_{0}.csv'.format(self.saved_file_name), 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar=',', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['id', 'date', 'price'])
        with open('data/price/{0}_idtoasin.csv'.format(self.saved_file_name), 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar=',', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['id', 'asin'])
        self.is_file_created = True

    def write_csv(self, id, product_asin, price_zip_list):
        with open('data/price/price_info_{0}.csv'.format(self.saved_file_name), 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar=',', quoting=csv.QUOTE_MINIMAL)
            for row in price_zip_list:
                csv_writer.writerow([id] + list(row))
        with open('data/price/{0}_idtoasin.csv'.format(self.saved_file_name), 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar=',', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow([id, product_asin])

    def get_prices(self, product_asin):
        products = self.keepa_api.query(product_asin)
        product = products[0]
        if 'NEW' not in product['data']:
            raise NoKeepaData
        price_zip_list = list(zip(product['data']['NEW_time'], product['data']['NEW']))
        return price_zip_list

    def save_csv(self, id, brand, model, *args):
        try:
            if not self.is_file_created:
                raise NoFile
            if args:
                note = ' '.join(list(args))
            else:
                note = ''
            product_asin = self.get_asin((' '.join([brand, model, note])).strip())
            price_zip_list = self.get_prices(product_asin)
            self.write_csv(id, product_asin, price_zip_list)
            print('Done!')
        except NoASIN:
            print('There are no ASIN for the keyword or Search server seems having some problems.')
        except NoKeepaData:
            print('There are no data in keepa for the ASIN or Search server seems having some problems.')
        except NoFile:
            print('please, make file first.')

'''
make_csv = PriceToCSV('2b63aol2vkmetj1lb1vii4a2knk9c07ik7bru5ihlctovg5t71mrtg3g48jfffd3')
make_csv.create_csv()


make_csv.save_csv('A23213D', '', '', 'Apple 15.4" MacBook Pro Laptop Computer with Retina Display & Force Touch Trackpad (Mid 2015)')
make_csv.create_csv('amazon')
make_csv.save_csv('D34124', 'apple', 'iphoneX')
'''
'''
make_csv = PriceToCSV('2b63aol2vkmetj1lb1vii4a2knk9c07ik7bru5ihlctovg5t71mrtg3g48jfffd3')
make_csv.create_csv()
make_csv.save_csv('', '', 'HP Pavilion 15t Premium Touch Laptop (Intel 8th Gen i7-8550U quad core, 8GB RAM, 1TB HDD + 128GB Sata SSD, 15.6 FHD 1920 x 1080, GeForce MX150, Backlit Keyboard, Win 10 Home) Sapphire Blue')
make_csv.save_csv('apple', 'iphoneX')
make_csv.save_csv('', '', 'HP Laptop ProBook 450 G5 (2ST09UT#ABA) Intel Core i5 8th Gen 8250U (1.60 GHz) 8 GB Memory 256 GB SSD Intel UHD Graphics 620 15.6" Windows 10 Pro 64-Bit')
make_csv.save_csv('HP', '450 G5 (2ST09UT#ABA)')


변경점
쓰기 전에 make_csv.create_csv 필요 (필요에 따라 파일 네임을 인자로 줄수있고, 기본값도있음)
make_price_csv의 이름이 save_csv로 변경
'''