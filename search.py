from flask import (Blueprint, render_template)

bp = Blueprint('search', __name__, url_prefix='/search')


@bp.route('/search', methods=['get'])
def process():
    # 검색하여 하나만 일치하면 result 페이지, 두개 이상 일치하면 product_view page
    return 'a'

@bp.route('/detail', methods=('get', 'post'))
def product_detail():
    return '검색 결과 페이지'

@bp.route('/list', methods=('get', 'post'))
def products():
    return render_template('search/products')

@bp.route('/all_list', methods=('get', 'post'))
def all_products():
    return render_template('search/all_products.html')
