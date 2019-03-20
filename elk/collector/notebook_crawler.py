import time
import re
import csv
from urllib.request import urlopen
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import StaleElementReferenceException

from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

import pricetocsv

class Newegg_Crawler:

    def __init__(self, url):
        firefox_profile = webdriver.FirefoxProfile()
        # firefox_profile.set_preference('permissions.default.image', 2) # 이미지 로딩 Disable
        # firefox_profile.set_preference('permissions.default.stylesheet', 2) # CSS 로딩 Disable
        # firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false') # Flashplayer Disable
        firefox_profile.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0')
        # os.environ["MOZ_HEADLESS"] = '1'
        self.driver = webdriver.Firefox(executable_path="./geckodriver", firefox_profile=firefox_profile)
        self.driver.get(url)
        time.sleep(5)
        self.pricecsv_exist = False
        self.reviewcsv_exist = False
        self.driver.refresh()

    def url_connect(self, url):
        html = urlopen(url)
        soup = BeautifulSoup(html, "lxml")

        return soup

    def driver_beautifulfy(self):
        
        html = self.driver.page_source
        html = BeautifulSoup(html, 'lxml')

        return html

    def action_chaining(self, target):
        print('action chaining start')
        print(self.driver)
        try:
            WebDriverWait(self.driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            self.driver.execute_script('window.scrollTo(1,'+str(target.location['y']-200)+')')
        except TimeoutException as e:
            print(e)
        except StaleElementReferenceException as e:
            print(e)
        except NoSuchElementException as e:
            print(e)

        action_chain = webdriver.ActionChains(self.driver)
        action_chain.move_to_element(target)
        action_chain.click(target)
        time.sleep(2)
        action_chain.perform()
        time.sleep(2)
        print('action chaining end')

        return self.driver

    def start_crawler(self):
        target_dict = {}
        titles = self.driver.find_elements_by_xpath("//a[@title='View Details']")

        return titles

    def img_crawler(self):
        time.sleep(5)
        product_img_id = self.driver.find_element_by_class_name('mainSlide').find_element_by_tag_name('img').get_attribute('id')

        html = self.driver.page_source
        product_page = BeautifulSoup(html, 'lxml')
        product_img = product_page.find('img', {'id': product_img_id})

        product_id = product_img_id[10:]
        if product_img_id[10] == '0':
            product_id = product_img_id[11:]

        product_imgsrc = product_img['src']

        spec_tab = self.driver.find_element_by_id('Details_Tab')
        print('poductID : %s\nproductImgSource : %s' % (product_id, product_imgsrc))

        return spec_tab

    def spec_crawler(self, make_csv):
        html = self.driver.page_source
        html = BeautifulSoup(html, 'lxml')
        product_page = html.find('div', {'id': 'detailSpecContent'})
        product_title = html.find('h1', {'id': 'grpDescrip_h'})
        product_page = product_page.find('fieldset')
        model_html = product_page.find_all('dl')
        model_dict = {}
        for data in model_html:
            model_dict[data.contents[0].string] = data.contents[1].string

        # Product Spec Crawling End

        if not self.pricecsv_exist:
            make_csv.create_csv()
            self.pricecsv_exist = True
        try:
            make_csv.save_csv(model_dict['Brand'], model_dict['Model'])
        except KeyError as e:
            make_csv.save_csv('', '', product_title.get_text())

        review_tab = self.driver.find_element_by_id('Community_Tab')

        return review_tab, model_dict

    def review_crawler(self, model_dict):
        try:
            f = open("review_info.csv", "r")
        except FileNotFoundError :
            f = open("review_info.csv", "a", encoding="utf-8", newline="")
            wr = csv.writer(f)
            wr.writerow(["Brand","Model","Star","Title","Date","Pros","Cons","Other","Voted_Y","Voted_N"])
        else:
            f = open("review_info.csv", "a", encoding="utf-8", newline="")
            wr = csv.writer(f)
        
        while(True):
            html = self.driver.page_source
            selectedItem = BeautifulSoup(html, "lxml")
            reviews = selectedItem.findAll("div", {"itemprop" : "review"})
            #print("==========",reviews)
            for review in reviews:
                #print(review.parent('div')[1])
                voted = review.find('div', {'class': 'comments-helpful'}).find('span').text
                parsing_voted = re.findall('[0-9]* out of [0-9]*', voted)
                if len(parsing_voted) != 0:
                    parsing_voted = re.findall('[0-9]*', parsing_voted[0])
                    print(parsing_voted)

                    voted_Y = parsing_voted[0]
                    voted_N = str(int(parsing_voted[-2]) - int(voted_Y))
                else:
                    voted_Y = 0
                    voted_N = 0
            
                existTitle = True
                try:
                    review.find("span", {"class" : "comments-title-content"}).text
                except AttributeError as e:
                     existTitle = False
                try:
                    reviewBodyForm = len(review.find("div", {"itemprop" : "reviewBody"})('p'))
                except TypeError as e:
                    reviewBodyForm = 0
                    pass

                if reviewBodyForm == 3:
                    if existTitle:
                        wr.writerow([model_dict["Brand"], \
                                model_dict["Model"], \
                                review.find("span", {"itemprop" : "ratingValue"}).text, \
                                review.find("span", {"class" : "comments-title-content"}).text, \
                                review.find("span", {"class" : "comments-time-right"})['content'], \
                                review.find("div", {"itemprop" : "reviewBody"})('p')[0].get_text(strip=True), \
                                review.find("div", {"itemprop" : "reviewBody"})('p')[1].get_text(strip=True), \
                                review.find("div", {"itemprop" : "reviewBody"})('p')[2].get_text(strip=True), \
                                voted_Y, \
                                voted_N])
                    else:
                        wr.writerow([model_dict["Brand"], \
                                     model_dict["Model"], \
                                     review.find("span", {"itemprop": "ratingValue"}).text, \
                                     None, \
                                     review.find("span", {"class": "comments-time-right"})['content'], \
                                     review.find("div", {"itemprop": "reviewBody"})('p')[0].get_text(strip=True), \
                                     review.find("div", {"itemprop": "reviewBody"})('p')[1].get_text(strip=True), \
                                     review.find("div", {"itemprop": "reviewBody"})('p')[2].get_text(strip=True), \
                                     voted_Y, \
                                     voted_N])
                elif reviewBodyForm == 2:
                    if existTitle:
                        wr.writerow([model_dict["Brand"], \
                                model_dict["Model"], \
                                review.find("span", {"itemprop" : "ratingValue"}).text, \
                                review.find("span", {"class" : "comments-title-content"}).text, \
                                review.find("span", {"class" : "comments-time-right"})['content'], \
                                review.find("div", {"itemprop" : "reviewBody"})('p')[0].get_text(strip=True), \
                                review.find("div", {"itemprop" : "reviewBody"})('p')[1].get_text(strip=True), \
                                None, \
                                voted_Y, \
                                voted_N])
                    else:
                        wr.writerow([model_dict["Brand"], \
                                model_dict["Model"], \
                                review.find("span", {"itemprop": "ratingValue"}).text, \
                                None, \
                                review.find("span", {"class": "comments-time-right"})['content'], \
                                review.find("div", {"itemprop": "reviewBody"})('p')[0].get_text(strip=True), \
                                review.find("div", {"itemprop": "reviewBody"})('p')[1].get_text(strip=True), \
                                None, \
                                voted_Y, \
                                voted_N])
                elif reviewBodyForm == 1:
                    if existTitle:
                        wr.writerow([model_dict["Brand"], \
                                 model_dict["Model"], \
                                 review.find("span", {"itemprop": "ratingValue"}).text, \
                                 review.find("span", {"class": "comments-title-content"}).text, \
                                 review.find("span", {"class": "comments-time-right"})['content'], \
                                 None, \
                                 None, \
                                 review.find("div", {"itemprop": "reviewBody"})('p')[0].get_text(strip=True), \
                                 voted_Y, \
                                 voted_N])
                    else:
                        wr.writerow([model_dict["Brand"], \
                                 model_dict["Model"], \
                                 review.find("span", {"itemprop": "ratingValue"}).text, \
                                 None, \
                                 review.find("span", {"class": "comments-time-right"})['content'], \
                                 None, \
                                 None, \
                                 review.find("div", {"itemprop": "reviewBody"})('p')[0].get_text(strip=True), \
                                 voted_Y, \
                                 voted_N])
                else: # 0 , -1
                    if existTitle:
                        wr.writerow([model_dict["Brand"], \
                                 model_dict["Model"], \
                                 review.find("span", {"itemprop": "ratingValue"}).text, \
                                 review.find("span", {"class": "comments-title-content"}).text, \
                                 review.find("span", {"class": "comments-time-right"})['content'], \
                                 None, \
                                 None, \
                                 None, \
                                 voted_Y,
                                 voted_N])
                    else:
                        print("mfr's comment DETECTED!!!")
            self.driver.execute_script("Biz.ProductReview2017.Pagination.nextbuttonClick()") # 다음 리뷰페이지로 넘김
            btn = selectedItem.find_all("button", {"onclick": "Biz.ProductReview2017.Pagination.nextbuttonClick()"})
            print("Next Page...")
            if (len(btn) == 0): # 다음 버튼이 아예 존재하지 않거나
                break
            elif (btn[0].get("disabled") == ""): # disabled 속성이면 루프 중단
                break




def main():
    product_index = 0
    make_csv = pricetocsv.PriceToCSV('2b63aol2vkmetj1lb1vii4a2knk9c07ik7bru5ihlctovg5t71mrtg3g48jfffd3')
    crawler = Newegg_Crawler('https://www.newegg.com/LCD-LED-Monitors/SubCategory/ID-20')

    titles = crawler.start_crawler()
    while(product_index < len(titles)):
        titles = crawler.start_crawler()

        crawler.action_chaining(titles[product_index])

        spec_tab = crawler.img_crawler()
        crawler.action_chaining(spec_tab)

        review_tab, model_dict = crawler.spec_crawler(make_csv)
        crawler.action_chaining(review_tab)
        crawler.review_crawler(model_dict)
        crawler.driver.back()
        product_index += 1

    crawler.driver.quit()

if __name__ == "__main__":
    main()
