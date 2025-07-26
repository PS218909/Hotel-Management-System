from flask import Blueprint, request
from ..util import *

api = Blueprint('api', __name__)

@api.route('/test')
def test_api():
    return {'status': 'working'}

@api.route('/search')
def search_customer():
    name = request.args.get('name', '')
    phone = request.args.get('phone', '')
    # res = search_query(CUSTOMER_DB, f'Name.str.startswith(\'{name}\') and Phone.str.contains(\'{phone}\')')
    res = search_customer_(name, phone)
    return res