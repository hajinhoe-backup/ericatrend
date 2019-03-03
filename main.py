from flask import (Blueprint, render_template)

bp = Blueprint('main', __name__, url_prefix='/')


@bp.route('/', methods=('get', 'post'))
def main():
    return render_template('main/main.html')
