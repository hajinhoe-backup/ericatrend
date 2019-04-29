from flask import (Blueprint, render_template)
import pymysql

bp = Blueprint('search', __name__, url_prefix='/search')


@bp.route('/search', methods=['get'])
def process():
    # SQL 커서를 전역으로 가지고 있도록 고쳐야함
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='22',
                                 db='notebook_db',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT `brand` FROM `product`"
            cursor.execute(sql, ())
            result = cursor.fetchall()
            for i in result:
                print(i)
    finally:
        connection.close()

    # 검색하여 하나만 일치하면 result 페이지, 두개 이상 일치하면 product_view page
    return 'a'

@bp.route('/detail', methods=('get', 'post'))
def product_detail():
    return render_template('search/product_detail.html')

@bp.route('/list', methods=('get', 'post'))
def products():
    return render_template('search/products')

@bp.route('/all_list', methods=('get', 'post'))
def all_products():
    return render_template('search/all_products.html')
