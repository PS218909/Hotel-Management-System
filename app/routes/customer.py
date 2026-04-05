from flask import Blueprint, request, jsonify, redirect, url_for, render_template, flash
from datetime import datetime

from app.services.customer import create_customer, alter_customer, delete_customer, get_customer_by_id, get_all_customers
from app.services.register import get_registers_by_customer
from app.services.transaction import get_transaction_by_register_id

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@customer_bp.route('/', methods=['GET'])
def list_customers():
    customers = get_all_customers()
    customer_list = [customer.to_dict() for customer in customers]
    return render_template('customer/index.html', customers=customer_list)

@customer_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    customer = get_customer_by_id(customer_id)
    if customer:
        registers = get_registers_by_customer(customer.id)
        transactions = []
        total_spent = 0
        total_visits = 0
        total_days = 0
        for reg in registers:
            for transaction in get_transaction_by_register_id(reg.id):
                transactions.append(transaction)
                total_spent += transaction.amount_paid
            total_visits += 1
            if reg.check_out:
                total_days += max((reg.check_out - reg.check_in).days, 1)
            else:
                total_days += max((datetime.now() - reg.check_in).days, 1)
        if total_visits:    
            analytics = {
                'total_spent': total_spent,
                'total_visits': total_visits,
                'total_days': total_days,
                'avg_stay': total_days / total_visits,
                'last_visit': registers[-1].check_in
            }
        else:
            analytics = {
                'total_spent': total_spent,
                'total_visits': total_visits,
                'total_days': total_days,
                'avg_stay': 0,
                'last_visit': []
            }
        return render_template('customer/profile.html', customer=customer, registers=registers, transactions=transactions, analytics=analytics)
    return jsonify({"message": "Customer not found"}), 404

@customer_bp.route('/create', methods=['POST', 'PUT'])
def create_new_customer():
    data = request.form or request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    address = data.get('address')
    id_type = data.get('id_type')
    id_detail = data.get('id_detail')

    customer = create_customer(name=name, email=email, phone=phone, address=address, id_type=id_type, id_detail=id_detail)
    if customer:
        return jsonify(customer.to_dict()), 200
    return jsonify({"message": "Failed to create customer", 'created': False}), 400

@customer_bp.route('/alter/<int:customer_id>', methods=['PUT', 'POST'])
def alter_existing_customer(customer_id):
    data = request.form or request.get_json()
    customer = alter_customer(customer_id, **data)
    if customer:
        return redirect(request.referrer)
    return jsonify({"message": "Customer not found"}), 404

@customer_bp.route('/delete/<int:customer_id>', methods=['DELETE'])
def delete_existing_customer(customer_id):
    success = delete_customer(customer_id)
    if success:
        return jsonify({"message": "Customer deleted successfully"}), 200
    return jsonify({"message": "Customer not found"}), 404