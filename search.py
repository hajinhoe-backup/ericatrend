from flask import (Blueprint)

bp = Blueprint('search', __name__, url_prefix='/search')


@bp.route('/result', methods=('get', 'post'))
def main():
    return '검색 결과 페이지'
