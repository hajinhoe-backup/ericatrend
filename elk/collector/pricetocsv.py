import keepa
import csv
import re
import os
import http.client, urllib.parse, json

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


업데이트 4.28
큐오팅 업데이트
기본값으로 create 시에 기존 파일이 있으면 append로 작동하게 됨.
0 값을 기록하지 않도록 변경함.
'''

class NoFile(Exception):
    pass


class NoKeepaData(Exception):
    pass

class NoASIN(Exception):
    pass


class BingSearch:
    def __init__(self):
        with open('access_keys.json') as file:
            data = json.load(file)
            self.key = data['bing_search_key']

        self.host = "api.cognitive.microsoft.com"
        self.path = "/bing/v7.0/search"

    def search(self, string):
        headers = {'Ocp-Apim-Subscription-Key': self.key}
        conn = http.client.HTTPSConnection(self.host)
        query = urllib.parse.quote(string)
        conn.request("GET", self.path + "?q=" + query, headers=headers)
        response = conn.getresponse()
        result = json.loads(response.read().decode("utf8"))
        if 'webPages' in result.keys() and 'value' in result['webPages'].keys():
            result = result['webPages']['value']
            return result
        else:
            return None


class PriceToCSV:
    def __init__(self):
        with open('access_keys.json') as file:
            data = json.load(file)
            keepa_accesskey = data['keepa_key']

        self.keepa_api = keepa.Keepa(keepa_accesskey)
        self.saved_file_name = 'price_info'
        self.is_file_created = False
        self.bing_search = BingSearch()

    def get_asin(self, product_name):
        # bing을 통해 아마존을 검색한다. None을 받을 경우 1회 재시도 한다.
        searched_items = self.bing_search.search('site:www.amazon.com ' + product_name)

        if not searched_items:
            searched_items = self.bing_search.search('site:www.amazon.com ' + product_name)

        for item in searched_items:
            if item['url']:
                searched_re = re.search('https://www.amazon.com/.+?/dp/(?P<ASIN>\w{10})', item['url'])
                if searched_re:
                    product_asin = searched_re.group('ASIN')
                    return product_asin

        raise NoASIN

    def create_csv(self, file_name=None, allow_append=True):
        if file_name:
            self.saved_file_name = file_name

        do_append = False

        if allow_append:
            if os.path.isfile('data/price/price_info_{0}.csv'.format(self.saved_file_name)):
                with open('data/price/price_info_{0}.csv'.format(self.saved_file_name), 'r', newline='') as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter='`', quotechar='"', quoting=csv.QUOTE_ALL)
                    for row in csv_reader: # for _ in _ 형식으로만 읽을 수 있음. 임의 접근이 안 됨.
                        if row == ['id', 'date', 'price']:
                            do_append = True
                        else:
                            do_append = False
                        break
            else:
                do_append = False

            if do_append and os.path.isfile('data/price/{0}_idtoasin.csv'.format(self.saved_file_name)):
                with open('data/price/{0}_idtoasin.csv'.format(self.saved_file_name), 'r', newline='') as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter='`', quotechar='"', quoting=csv.QUOTE_ALL)
                    for row in csv_reader:  # for _ in _ 형식으로만 읽을 수 있음. 임의 접근이 안 됨.
                        if row == ['id', 'asin']:
                            do_append = True
                        else:
                            do_append = False
                        break
            else:
                do_append = False

        if not do_append:
            with open('data/price/price_info_{0}.csv'.format(self.saved_file_name), 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter='`', quotechar='"', quoting=csv.QUOTE_ALL)
                csv_writer.writerow(['id', 'date', 'price'])
            with open('data/price/{0}_idtoasin.csv'.format(self.saved_file_name), 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter='`', quotechar='"', quoting=csv.QUOTE_ALL)
                csv_writer.writerow(['id', 'asin'])

        self.is_file_created = True

    def write_csv(self, id, product_asin, price_zip_list):
        with open('data/price/price_info_{0}.csv'.format(self.saved_file_name), 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter='`', quotechar='"', quoting=csv.QUOTE_ALL)
            for row in price_zip_list:
                if row[1] == row[1] and row[1] != 0: # Nan 이면 자기 자신과 비교했을 때, False가 나옵니다.
                    csv_writer.writerow([id] + list(row))
        with open('data/price/{0}_idtoasin.csv'.format(self.saved_file_name), 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter='`', quotechar='"', quoting=csv.QUOTE_ALL)
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
            print(product_asin, 'Done!')
        except NoASIN:
            print('There are no ASIN for the keyword or Search server seems having some problems.')
        except NoKeepaData:
            print('There are no data in keepa for the ASIN or Search server seems having some problems.')
        except NoFile:
            print('please, make file first.')

make_csv = PriceToCSV()
make_csv.create_csv()


make_csv.save_csv('A23213D', '', '', 'Apple 15.4" MacBook Pro Laptop Computer with Retina Display & Force Touch Trackpad (Mid 2015)')
make_csv.create_csv('amazon')
make_csv.save_csv('D34124', 'apple', 'iphoneX')

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