from flask import Blueprint, request, jsonify, redirect, url_for, render_template, flash
from app.services.transaction import create_transaction, get_transaction_by_id, get_all_transactions, delete_transaction, update_transaction
from app.util.helper import calculate_time_difference, calculate_total_balance, send_webhook_alert

transaction_bp = Blueprint('transaction', __name__, url_prefix='/account')

@transaction_bp.route('/')
def list_transactions():
    transactions = get_all_transactions()
    return render_template('transaction/index.html', transactions=transactions)

@transaction_bp.route('/<int:transaction_id>')
def form_transaction(transaction_id):
    transaction = get_transaction_by_id(transaction_id)
    if not transaction:
        flash('Transaction not found', 'error')
        return redirect(url_for('transaction.list_transactions'))
    return jsonify({'data': transaction, 'message': 'Transaction fetched successfully'}), 200

@transaction_bp.route('/create', methods=['POST'])
def create_transaction_page():
    data = request.form
    register_id = data.get('register_id')
    amount_paid = data.get('amount_paid')
    payment_method = data.get('payment_method')
    transaction = create_transaction(register_id=register_id, amount_paid=amount_paid, payment_method=payment_method)
    if transaction:
        register = transaction.register
        alert_dict = {
                    'Room No.': register.room.room_number,
                    'Name': register.customer.name,
                    'Address': register.customer.address,
                    'Phone': register.customer.phone,
                    'Check In': register.check_in.strftime('%d-%m-%Y %H:%M'),
                    'Check Out': register.check_out.strftime('%d-%m-%Y %H:%M') if register.check_out else '',
                    'Amount Paid': register.total_paid,
                    'Remaining Balance': calculate_total_balance(register.rent_per_day, register.check_in, register.check_out) - register.total_paid
                }
        send_webhook_alert({
            'title': '💰 Add Payment', 
            'description': '\n'.join('**'+str(k)+': **'+str(v) for k, v in alert_dict.items()),
        })
        flash('Transaction Added Successfully!', 'success')
        return redirect(request.referrer)
    return jsonify({"message": "Failed to create transaction"}), 400

@transaction_bp.route('/delete/<int:transaction_id>')
def delete_transaction_page(transaction_id):
    success = delete_transaction(transaction_id)
    if success:
        flash('Transaction deleted successfully!', 'success')
    else:
        flash('Failed to delete transaction', 'error')
    return jsonify({'success': success})

@transaction_bp.route('/update/<int:transaction_id>', methods=['POST'])
def update_transaction_page(transaction_id):
    data = request.form
    amount_paid = data.get('amount_paid')
    payment_method = data.get('payment_method')
    updated_transaction = update_transaction(transaction_id, amount_paid=amount_paid, payment_method=payment_method)
    if updated_transaction:
        register = updated_transaction.register
        alert_dict = {
                    'Room No.': register.room.room_number,
                    'Name': register.customer.name,
                    'Address': register.customer.address,
                    'Phone': register.customer.phone,
                    'Check In': register.check_in.strftime('%d-%m-%Y %H:%M'),
                    'Check Out': register.check_out.strftime('%d-%m-%Y %H:%M') if register.check_out else '',
                    'Amount Paid': register.total_paid,
                    'Remaining Balance': calculate_total_balance(register.rent_per_day, register.check_in, register.check_out) - register.total_paid
                }
        send_webhook_alert({
            'title': '✏️ Update Payment', 
            'description': '\n'.join('**'+str(k)+': **'+str(v) for k, v in alert_dict.items()),
        })
        flash('Transaction updated successfully!', 'success')
        return jsonify({'message': 'Transaction updated successfully!'}), 200
    return jsonify({"message": "Failed to update transaction"}), 400