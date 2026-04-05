from flask import Blueprint, request, jsonify
from app.services.customer import search_customers_by_multiple_fields, get_customer_by_id
from app.services.register import get_register_by_current_stay, get_register_by_id, search_registers, get_registers_by_customer
from app.services.transaction import get_all_transaction_api
from app.services.room import get_all_rooms
from app.util.helper import register_records_to_array, transactions_to_array

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/search/discord', methods=['GET'])
def _search_discord():
    return jsonify(get_all_rooms())

@api_bp.route('/search/customer', methods=['GET'])
def search_customers():
    name = request.args.get('name')
    email = request.args.get('email')
    phone = request.args.get('phone')
    address = request.args.get('address')
    id_type = request.args.get('id_type')
    id_detail = request.args.get('id_detail')

    customers = search_customers_by_multiple_fields(name=name, email=email, phone=phone, address=address, id_type=id_type, id_detail=id_detail)
    customer_list = [{
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "id_type": customer.id_type,
        "id_detail": customer.id_detail,
    } for customer in customers]
    return jsonify(customer_list)

@api_bp.route('/get/register/customer', methods=['GET'])
def get_register_customers():
    room_id = request.args.get('room_id', None)
    register_id = request.args.get('register_id', None)
    register = None
    if room_id:
        register = get_register_by_current_stay(room_id)
    if register_id:
        register = get_register_by_id(register_id)
    if register:
        customers = register.get_customer_list()
        customer_list = []
        for k, v in customers.items():
            if v['id'] is not None:
                customer_list.append(get_customer_by_id(v['id']).to_dict()) # type: ignore
        return jsonify(customer_list)
    return jsonify({'message': 'Not Found'})

@api_bp.route('/search/register')
def search_register():
    registers = search_registers(**request.args)
    if registers:
        selected = register_records_to_array(registers)
        return jsonify(selected)
    else: 
        return []

@api_bp.route('/search/transaction')
def search_transaction():
    transactions = get_all_transaction_api(**request.args)
    if transactions:
        transactions = transactions_to_array(transactions)
        return jsonify(transactions)
    return jsonify({})

@api_bp.route('/search/customer/history')
def customer_history():
    registers = get_registers_by_customer(request.args.get('customer_id', 1))
    if registers:
        selected = register_records_to_array(registers)
        return jsonify(selected)
    else:
        return []