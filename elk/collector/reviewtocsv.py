import argparse
import time
import re
import os
import csv
from urllib.request import urlopen
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

import pricetocsv


def urlConnect(url):
    print(url)
    html = urlopen(url)
    soup = BeautifulSoup(html, "lxml")
    return soup

def extractSpec(driver, productID):
    print("exractSpec START")
    driver.get(
            "https://www.newegg.com/Product/Product.aspx?Page=2&reviews=all&Item=" + productID + "&Pagesize=100&IsFeedbackTab=true")
    try:  # Details_Tab 로드까지 대기
        button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "Details_Tab")))
    except TimeoutException as e:
        print(e," : Cannot load a Details Tab..")
    html_detail = driver.page_source
    soup_detail = BeautifulSoup(html_detail, 'lxml')

    html = soup_detail.find('div', {'id':'detailSpecContent'})
    html = html.find('fieldset')
    model_html = html.find_all('dl')
    model_dict = {}
    for data in model_html:
        model_dict[data.contents[0].string] = data.contents[1].string
    
    make_csv = pricetocsv.PriceToCSV('2b63aol2vkmetj1lb1vii4a2knk9c07ik7bru5ihlctovg5t71mrtg3g48jfffd3')
    make_csv.create_csv()
    make_csv.save_csv(model_dict['Brand'], model_dict['Model'])

    driver.find_element_by_id("Community_Tab").click()
    return driver, model_dict

def productList(keyword, All=None):
    count = 0
    productIds = []
    keyword = keyword.replace(" ", "%20")
    productList = urlConnect(
            "https://www.newegg.com/Product/ProductList.aspx?Submit=ENE&DEPA=0&Order=BESTMATCH&Page=1&Description=" + keyword)

    titles = productList.findAll("a", {"title": "View Details"}) # 제품 타이틀이 포함된 태그 가져오기
    if All:
        for title in titles:
            product = re.findall("-_-.*-_-Product",title['href'])
            if len(product) != 0:  # 정규식에 매칭되는 경우
                productIds.append(product[0][3:-10])
    else :
        product = re.findall("-_-.*-_-Product", titles[0]['href'])
        productIds.append(product[0][3:-10])

    return productIds

def productDetails(productID):
    startTime1 = time.time()
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference('permissions.default.image', 2) # 이미지 로딩 Disable
    firefox_profile.set_preference('permissions.default.stylesheet', 2) # CSS 로딩 Disable
    firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false') # Flashplayer Disable
    firefox_profile.set_preference('browser.cache.disk.enable', True)
    firefox_profile.set_preference("network.cookie.cookieBehavior", 2) # Cookie Disable

    os.environ["MOZ_HEADLESS"] = '1'
    startTime = time.time()
    # binary = FirefoxBinary("C:\\Program Files\\Mozilla Firefox\\firefox.exe") # for Window
    driver = webdriver.Firefox(executable_path="./geckodriver", firefox_profile=firefox_profile)
    driver, model_dict = extractSpec(driver, productID)

    endTime = time.time() - startTime
    print("드라이버 구동시간 : ", endTime)
    startTime = time.time()

    productTitle = driver.find_element_by_id("FeedBackShortTitle").text
    f = open("./data/review_info.csv", "a", encoding="utf-8", newline="")
    wr = csv.writer(f)
    wr.writerow(["Brand","Model","Star","Title","Date","Pros","Cons","Other"])

    while(True):
        try:
            dropdown = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "reviewPageSize")))
        except TimeoutException as e:
            print(e," : Loading took too much time...")
        html = driver.page_source
        selectedItem = BeautifulSoup(html, "lxml")
        reviews = selectedItem.findAll("div", {"itemprop" : "review"})
        for review in reviews:
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
                            review.find("div", {"itemprop" : "reviewBody"})('p')[2].get_text(strip=True)])
                else:
                    wr.writerow([model_dict["Brand"], \
                                 model_dict["Model"], \
                                 review.find("span", {"itemprop": "ratingValue"}).text, \
                                 "", \
                                 review.find("span", {"class": "comments-time-right"})['content'], \
                                 review.find("div", {"itemprop": "reviewBody"})('p')[0].get_text(strip=True), \
                                 review.find("div", {"itemprop": "reviewBody"})('p')[1].get_text(strip=True), \
                                 review.find("div", {"itemprop": "reviewBody"})('p')[2].get_text(strip=True)])
            elif reviewBodyForm == 2:
                if existTitle:
                    wr.writerow([model_dict["Brand"], \
                            model_dict["Model"], \
                            review.find("span", {"itemprop" : "ratingValue"}).text, \
                            review.find("span", {"class" : "comments-title-content"}).text, \
                            review.find("span", {"class" : "comments-time-right"})['content'], \
                            review.find("div", {"itemprop" : "reviewBody"})('p')[0].get_text(strip=True), \
                            review.find("div", {"itemprop" : "reviewBody"})('p')[1].get_text(strip=True), \
                            ""])
                else:
                    wr.writerow([model_dict["Brand"], \
                            model_dict["Model"], \
                            review.find("span", {"itemprop": "ratingValue"}).text, \
                            "", \
                            review.find("span", {"class": "comments-time-right"})['content'], \
                            review.find("div", {"itemprop": "reviewBody"})('p')[0].get_text(strip=True), \
                            review.find("div", {"itemprop": "reviewBody"})('p')[1].get_text(strip=True), \
                            ""])
            elif reviewBodyForm == 1:
                if existTitle:
                    wr.writerow([model_dict["Brand"], \
                             model_dict["Model"], \
                             review.find("span", {"itemprop": "ratingValue"}).text, \
                             review.find("span", {"class": "comments-title-content"}).text, \
                             review.find("span", {"class": "comments-time-right"})['content'], \
                             "", \
                             "", \
                             review.find("div", {"itemprop": "reviewBody"})('p')[0].get_text(strip=True)])
                else:
                    wr.writerow([model_dict["Brand"], \
                             model_dict["Model"], \
                             review.find("span", {"itemprop": "ratingValue"}).text, \
                             "", \
                             review.find("span", {"class": "comments-time-right"})['content'], \
                             "", \
                             "", \
                             review.find("div", {"itemprop": "reviewBody"})('p')[0].get_text(strip=True)])
            else: # 0 , -1
                if existTitle:
                    wr.writerow([model_dict["Brand"], \
                             model_dict["Model"], \
                             review.find("span", {"itemprop": "ratingValue"}).text, \
                             review.find("span", {"class": "comments-title-content"}).text, \
                             review.find("span", {"class": "comments-time-right"})['content'], \
                             "", \
                             "", \
                             ""])
                else:
                    print("mfr's comment DETECTED!!!")
        driver.execute_script("Biz.ProductReview2017.Pagination.nextbuttonClick()") # 다음 리뷰페이지로 넘김
        btn = selectedItem.find_all("button", {"onclick": "Biz.ProductReview2017.Pagination.nextbuttonClick()"})
        print("Next Page...")
        if (len(btn) == 0): # 다음 버튼이 아예 존재하지 않거나
            break
        elif (btn[0].get("disabled") == ""): # disabled 속성이면 루프 중단
            break

    f.close()
    print("===================================")
    print("Brand : %s" % (model_dict['Brand']))
    print("Model : %s" % (model_dict['Model']))
    print("%s reviews added." % (len(reviews)))
    print("===================================")
    driver.quit()
    endTime = time.time() - startTime
    print("리뷰 파싱시간 : " ,endTime)

    endTime1 = time.time() - startTime1
    print("총 가동 시간 : ",endTime1)

    return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ProductName", type=str, help="The Product you want to find")
    parser.add_argument("--all", action="store_true", help="If you want to find all of related result, add this option")

    args = parser.parse_args()

    if args.all:
        productId = productList(args.ProductName, All=True)
    elif args.ProductName:
        productId = productList(args.ProductName)

    productDetails(productId[0]) 



if __name__ == "__main__":
    main()
