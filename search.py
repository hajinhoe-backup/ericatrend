from flask import (Blueprint, render_template, request, url_for, redirect)
import pymysql

bp = Blueprint('search', __name__, url_prefix='/search')


@bp.route('/search', methods=['get'])
def process():
    def generate_sql(string):
        # 대소문자 구분은 테이블에서 환경설정으로 처리가 가능함.
        keywords = string.split()
        sql = ''
        for n in range(len(keywords)):
            sql += '`brand` LIKE "%{0}%" or `model` LIKE "%{0}%"'.format(keywords[n])
            if not n == len(keywords) - 1:
                sql += " or "
        return sql

    keyword = request.args.get('search_words')
    if 'page' in request.args.keys():
        page = int(request.args.get('page'))
    else:
        page = 1

    # SQL 커서를 전역으로 가지고 있도록 고쳐야함
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='dekiru6120',
                                 db='notebook_db',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT `newegg_id`, `brand`, `model` FROM `product` WHERE " + generate_sql(keyword) + " LIMIT {0}, {1}".format((page-1)*10, 10)
            cursor.execute(sql)
            result = cursor.fetchall()
    finally:
        connection.close()

    if len(result) == 1: # 검색결과가 하나만 있는 경우 바로 제품 상세 페이지로 간다.
        return product_detail(newegg_id=result[0]['newegg_id'])
    else: # 검색 결과가 여러개인 경우 제품 리스트로 간다.
        return products(keyword, page, result)

    # 검색하여 하나만 일치하면  페이지, 두개 이상 일치하면 product_view page

@bp.route('/detail', methods=['get'])
def product_detail(newegg_id=None):
    if not newegg_id: # 프로그램 순서상으로 자동으로 받아왔을 경우가 아닌 경우
        newegg_id = request.args.get('newegg_id')
    # SQL 커서를 전역으로 가지고 있도록 고쳐야함
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='dekiru6120',
                                 db='notebook_db',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT `newegg_id`, `brand`, `model` FROM `product` WHERE `newegg_id` = %s"
            cursor.execute(sql, (newegg_id, ))
            result = cursor.fetchone()
    finally:
        connection.close()
    return render_template('search/product_detail.html', product=result)

@bp.route('/list', methods=('get', 'post'))
def products(keyword, page, products_info):
    return render_template('search/products.html', keyword=keyword, page=page, products_info=products_info)

@bp.route('/all_list', methods=('get', 'post'))
def all_products():
    return render_template('search/all_products.html')
