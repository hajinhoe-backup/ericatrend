from flask import (Blueprint, render_template, request, url_for, send_file)
from pytrends.request import TrendReq
import pymysql
import os
import re

bp = Blueprint('search', __name__, url_prefix='/search')


@bp.route('/search', methods=['get'])
def process():
    def generate_sql(string):
        # 대소문자 구분은 테이블에서 환경설정으로 처리가 가능함.
        keywords = string.split()
        sql = ''
        for n in range(len(keywords)):
            sql += '(`brand` LIKE "%{0}%" or `model` LIKE "%{0}%")'.format(keywords[n])
            if not n == len(keywords) - 1:
                sql += " and "
        return sql


    keyword = request.args.get('search_words')
    if 'page' in request.args.keys():
        page = int(request.args.get('page'))
    else:
        page = 1


    # SQL 커서를 전역으로 가지고 있도록 고쳐야함
    connection = pymysql.connect(host='ericatrend.net',
                                 user='erica',
                                 password='hosugongwon',
                                 db='notebook_db',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    with connection.cursor() as cursor:
        # Read a single record
        sql = "SELECT * FROM `for_presentation_products` WHERE " + generate_sql(keyword) + " LIMIT {0}, {1}".format((page-1)*10, 10)
        cursor.execute(sql)
        result = cursor.fetchall()

    if len(result) == 1 and page == 1: # 검색결과가 하나만 있는 경우 바로 제품 상세 페이지로 간다.
        connection.close()
        return product_detail(newegg_id=result[0]['newegg_id'])
    else: # 검색 결과가 여러개인 경우 제품 리스트로 간다.
        try:
            with connection.cursor() as cursor:
                # Read a single record
                sql = "SELECT count(*) FROM `for_presentation_products` WHERE " + generate_sql(keyword)
                cursor.execute(sql)
                number_of_product = cursor.fetchone()['count(*)']
        finally:
            connection.close()
        expression = re.compile('\d+\.?\d*')
        for item in result:
            if item['price']:
                item['price'] = '{:0.0f} 달러'.format(item['price'])
            if item['weight']:
                value = expression.match(item['weight'])
                if value:
                    item['weight'] = '{:0.2f}kg'.format(float(value[0])*0.453592)
        return products(keyword, page, number_of_product, result)

    # 검색하여 하나만 일치하면  페이지, 두개 이상 일치하면 product_view page

@bp.route('/related_queries', methods=['get'])
def get_related_queries():
    string = request.args.get('keyword')
    try:
        pytrend_session = TrendReq(hl='en-US', tz=120)
        pytrend_session.build_payload(kw_list=[string], cat=30, timeframe='today 12-m', geo='', gprop='')
        related_keyword = pytrend_session.related_queries()
        if related_keyword[string]['top'] is None:
            raise KeyError

    except KeyError as e: # 키워드가 입력되지 않은 경우
        return ''

    return render_template('search/delayed/related_keywords.html', related_keyword=related_keyword[string]['top']['query'])



@bp.route('/detail', methods=['get'])
def product_detail(newegg_id=None):
    def related_keyword(string):
        try:
            pytrend_session = TrendReq()
            pytrend_session.build_payload(kw_list=[string])
            related_keyword = pytrend_session.related_queries()
        except KeyError as e: # 키워드가 입력되지 않은 경우
            related_keyword[string]['top'] = None
            related_keyword[string]['rising'] = None
            return related_keyword[string]
        return related_keyword[string]

    if not newegg_id: # 프로그램 순서상으로 자동으로 받아왔을 경우가 아닌 경우
        newegg_id = request.args.get('newegg_id')
    # SQL 커서를 전역으로 가지고 있도록 고쳐야함
    connection = pymysql.connect(host='ericatrend.net',
                                 user='erica',
                                 password='hosugongwon',
                                 db='notebook_db',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT * FROM `for_presentation_products` WHERE `newegg_id` = %s"
            cursor.execute(sql, (newegg_id, ))
            result = cursor.fetchone()
            sql = "SELECT `title`, `date`, `pros`, `cons`, `star`, `helpful`, `unhelpful` FROM `review` WHERE `newegg_id`= %s ORDER BY `date` LIMIT 10"
            cursor.execute(sql, (newegg_id,))
            reviews = cursor.fetchall()
    finally:
        connection.close()

    try:
        keyword = "".join([result['brand'], " ", result['model']]) 
        related_keyword = related_keyword(keyword)
    except KeyError as e:
        if 'brand' not in result.keys(): related_keyword = related_keyword(result['brand'])
        if 'model' not in result.keys(): related_keyword = related_keyword(result['model'])

    expression = re.compile('\d+\.?\d*')
    if result['weight']:
        value = expression.match(result['weight'])
        if value:
            result['weight'] = '{:0.2f}kg'.format(float(value[0]) * 0.453592)

    return render_template('search/product_detail.html', product=result, reviews=reviews, related_keyword=related_keyword)

@bp.route('/detail/word_cloud', methods=['get'])
def delayed_word_cloud():
    newegg_id = request.args.get('newegg_id')
    return render_template('search/delayed/word_cloud.html', newegg_id=newegg_id)

@bp.route('/list', methods=('get', 'post'))
def products(keyword, now_page, number_of_product, products_info):
    last_page = number_of_product/10

    # 숫자를 올림 처리합니다.
    if int(last_page) == last_page:
        last_page = int(last_page)
    else:
        last_page = int(last_page) + 1
    # 화면에 표시할 페이지 리스트를 생성합니다. 앞에 두개, 현재 페이지, 뒤에 두개로 나타내며,
    # 앞에가 부족하면 뒤에 그만큼, 뒤에가 부족하면 앞에 그만큼 표시합니다.
    if now_page < 3:
        pages = [i for i in range(1, min(6, last_page + 1))]
    elif now_page > last_page - 3:
        pages = [i for i in range(now_page - 2, min(last_page + 1, now_page + 3))]
    else:
        pages = [i for i in range(now_page - 2, now_page + 3)]
    return render_template('search/products.html', keyword=keyword, last_page=last_page, pages=pages, now_page=now_page, products_info=products_info)

@bp.route('/all_list', methods=('get', 'post'))
def all_products():
    return render_template('search/all_products.html')

@bp.route('/compare', methods=('get', 'post'))
def compare():
    if request.args.get('compare_type'):
        compare_type = request.args.get('compare_type')
    else:
        compare_type = None

    parameters = []

    if compare_type == 'brand':
        parameters.append(request.args.get('first_brand'))
        parameters.append(request.args.get('second_brand'))
        parameters.append(request.args.get('third_brand'))
        parameters.append(request.args.get('forth_brand'))
    elif compare_type == 'price':
        parameters.append(request.args.get('first_range').split(';'))
        parameters.append(request.args.get('second_range').split(';'))


    connection = pymysql.connect(host='ericatrend.net',
                                 user='erica',
                                 password='hosugongwon',
                                 db='notebook_db',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT DISTINCT `brand` FROM `for_presentation_products` WHERE `brand` != '' ORDER BY `brand` ASC"
            cursor.execute(sql)
            brands = cursor.fetchall()
    finally:
        connection.close()
    return render_template('search/compare.html', brands=brands, compare_type=compare_type, parameters=parameters)

@bp.route('/compare/process', methods=['post'])
def compare_process():
    if request.form['compare_type']:
        compare_type = request.form['compare_type']
    else:
        compare_type = None

    parameters = []

    if compare_type == 'brand':
        parameters.append(request.form['first_brand'])
        parameters.append(request.form['second_brand'])
        parameters.append(request.form['third_brand'])
        parameters.append(request.form['forth_brand'])
    elif compare_type == 'price':
        parameters.append(request.form['first_range'].split(';'))
        parameters.append(request.form['second_range'].split(';'))


    connection = pymysql.connect(host='ericatrend.net',
                                 user='erica',
                                 password='hosugongwon',
                                 db='notebook_db',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT DISTINCT `brand` FROM `for_presentation_products` WHERE `brand` != '' ORDER BY `brand` ASC"
            cursor.execute(sql)
            brands = cursor.fetchall()
    finally:
        connection.close()

    return render_template('search/compare_result.html', compare_type=compare_type, parameters=parameters)

@bp.route('/images/<path:image_name>') # 이미지 라우팅
def get_image(image_name):
    if os.path.exists('static/images/'+image_name):
        return send_file('static/images/'+image_name)
    else:
        return send_file('static/images/no_image_avail.png')