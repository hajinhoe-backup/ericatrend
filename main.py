from flask import (Blueprint)

bp = Blueprint('main', __name__, url_prefix='/')


@bp.route('/', methods=('get', 'post'))
def main():
    return '검색창이 있는 메인화면'
