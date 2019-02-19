from flask import Flask
from flask import render_template
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

app = Flask(__name__)

def urlConnect(url):
    print(url)
    html = urlopen(url)
    soup = BeautifulSoup(html, "lxml")
    return soup

@app.route('/')
def hello_world():
    print("hi")
    return render_template("index.html")

@app.route('/<keyword>/<pageNum>')
def productList(keyword, pageNum):
    def findProductId(productList):
        count = 0
        productDict = dict()
        titles = productList.findAll("a", {"class": "item-title"}, {"title": "View Details"}) # 제품 타이틀이 포함된 태그 가져오기

        for title in titles:
            productId = re.findall("-_-.*-_-Product", title['href'])
            if len(productId) != 0:  # 정규식에 매칭되는 경우
                productId = (productId[0][3:-10])
                productDict[count + 1] = {"title": title.get_text(strip=True), "link": title['href'], "id": productId, "img": title.parent.find_previous()['src']}
                count += 1
            else:
                continue
        return productDict
    keyword = keyword.replace(" ", "%20")
    productList = urlConnect(
        "https://www.newegg.com/Product/ProductList.aspx?Submit=ENE&DEPA=0&Order=BESTMATCH&Page=" + str(
            pageNum) + "&Description=" + keyword)
    productDict = findProductId(productList)

    return render_template("products.html", productDict=productDict, keyword=keyword, nextpageNum=int(pageNum)+1, prevpageNum=int(pageNum)-1)

@app.route('/review/<productID>')
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
    # binary = FirefoxBinary("C:\\Program Files\\Mozilla Firefox\\firefox.exe")
    executable_path = "./geckodriver"
    driver = webdriver.Firefox(executable_path=executable_path, firefox_profile=firefox_profile)

    cacheDriver = driver.application_cache
    endTime = time.time() - startTime
    print("드라이버 구동시간 : ", endTime)

    driver.get(
        "https://www.newegg.com/Product/Product.aspx?Page=2&reviews=all&Item=" + productID + "&Pagesize=100&IsFeedbackTab=true")
    try: # 해당 ID 컴포넌트 로딩까지 최대 5초 대기, js 수행 후 작업을 시작하기 위해 (js로 AllRelatedProduct 체크박스가 체크됨)
        title = WebDriverWait(driver, 5) \
            .until(EC.presence_of_element_located((By.ID, "prAllRelatedProduct")))
        print(title.text)

    except TimeoutException:
        isExistReview = driver.execute_script("return Biz.ProductReview2017.PageUrlconfig['Pagesize']")  # 리뷰 페이지 수를 확인
        if (isExistReview == ""):                     # 리뷰 페이지 값이 들어있지 않으면,
            driver.quit()                             # 드라이버를 종료하고,
            return render_template("noReviews.html")  # 안내페이지로 이동
        else: # 리뷰는 존재하지만 수가 적어서 2개 이상의 페이지가 없는 경우 / 일부 리뷰에서 버튼자체가 없는 페이지가 보임 / 파싱은 진행가능
            print("All Related Product Reviews 체크박스가 존재하지 않습니다.")
    finally:
        pass
    productTitle = driver.find_element_by_id("grpDescrip_"+productID).text
    startTime = time.time()
    f = open("./data/review_info.csv", "a", encoding="utf-8", newline="")
    wr = csv.writer(f)

    while(True): #
        html = driver.page_source
        selectedItem = BeautifulSoup(html, "lxml")
        reviews = selectedItem.findAll("div", {"class" : "comments-cell"}, {"itemprop" : "review"})
        for review in reviews:
            try: # customer review
                wr.writerow([productTitle, \
                    review.find("span", {"itemprop" : "ratingValue"}).text, \
                    review.find("span", {"class" : "comments-title-content"}).text, \
                    review.find("span", {"class" : "comments-time-right"})['content'], \
                    review.find("div", {"itemprop" : "reviewBody"})('p')[0].get_text(strip=True), \
                    review.find("div", {"itemprop" : "reviewBody"})('p')[1].get_text(strip=True), \
                    review.find("div", {"itemprop" : "reviewBody"})('p')[2].get_text(strip=True)])
            except AttributeError as e: # MFr's response
                print("mfs's resoponse : ",e)
                pass
            except IndexError as e: # No Other Thoughts
                print("there is no other thoughts section : ",e)
                wr.writerow([productTitle, \
                    review.find("span", {"itemprop" : "ratingValue"}).text, \
                    review.find("span", {"class" : "comments-title-content"}).text, \
                    review.find("span", {"class" : "comments-time-right"})['content'], \
                    review.find("div", {"itemprop" : "reviewBody"})('p')[0].get_text(strip=True), \
                    review.find("div", {"itemprop" : "reviewBody"})('p')[1].get_text(strip=True), \
                    "None"])
        driver.execute_script("Biz.ProductReview2017.Pagination.nextbuttonClick()") # 다음 리뷰페이지로 넘김
        btn = selectedItem.find_all("button", {"onclick": "Biz.ProductReview2017.Pagination.nextbuttonClick()"})
        print("test")
        if (len(btn) == 0): # 다음 버튼이 아예 존재하지 않거나
            break
        elif (btn[0].get("disabled") == ""): # disabled 속성이면 루프 중단
            break
    f.close()

    driver.quit()
    endTime = time.time() - startTime
    print("리뷰 파싱시간 : " ,endTime)

    endTime1 = time.time() - startTime1
    print("총 가동 시간 : ",endTime1)


    return render_template("reviews.html")

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
