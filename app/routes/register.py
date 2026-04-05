from flask import Blueprint, request, jsonify, redirect, url_for, render_template, flash
from app.services.register import get_register_by_id, alter_register, get_all_registers, delete_all_record
from app.services.transaction import get_transaction_by_register_id, get_all_transaction_api
from app.services.room import get_all_rooms
from typing import Any
from datetime import datetime
from app.util.helper import calculate_total_balance, register_records_to_array, calculate_time_difference, send_webhook_alert, generate_image

register_bp = Blueprint('register', __name__, url_prefix='/register')
@register_bp.route('/')
def list_registers():
    return render_template('register/index.html')

@register_bp.route('/<int:register_id>', methods=['GET', 'POST'])
def form_register(register_id):
    register = get_register_by_id(register_id)
    if not register:
        flash('Register not found', 'error')
        return redirect(url_for('register.list_registers'))
    if not register.check_out:
        return redirect(url_for('room.form_room', room_no=register.room.room_number))
    if request.method == 'POST':
        data: dict[str, Any] = dict(request.form)
        data.update({
            'check_out': datetime.strptime(data.get('check_out', ''), '%Y-%m-%dT%H:%M') if data.get('check_out', None) else None,
            'check_in': datetime.strptime(data.get('check_in', datetime.now().strftime('%Y-%m-%dT%H:%M')), '%Y-%m-%dT%H:%M'),
            'ac': True if data.get('ac') == 'true' else False, 
        })
        register = alter_register(register_id, **data)
        if register:
            alert_dict = {
                'Room No.': register.room.room_number,
                'Name': register.customer.name,
                'Address': register.customer.address,
                'Phone': register.customer.phone,
                'Check In': register.check_in.strftime('%d-%m-%Y %H:%M'),
                'Check Out': register.check_out.strftime('%d-%m-%Y %H:%M'),
                'Amount Paid': register.total_paid,
                'Remaining Balance': calculate_total_balance(register.rent_per_day, register.check_in, register.check_out) - register.total_paid
            }
            send_webhook_alert({
                'title': '✏️ Update Details - Register ID: ' + str(register_id), 
                'description': '\n'.join('**'+str(k)+': **'+str(v) for k, v in alert_dict.items()),
            })
        flash('Register details updated successfully', 'success')
        return redirect(request.referrer)
    else:
        # Logic to display a specific register's details
        payments = get_transaction_by_register_id(register.id)
        tp = calculate_time_difference(register.check_in)
        register.time_passed = f'{tp[0]} Days {round(float(tp[1]), 1)} Hours'
        register.total_amount = calculate_total_balance(register.rent_per_day, register.check_in, register.check_out)
        register.remaining_balance = register.total_amount - register.total_paid
        payments = get_transaction_by_register_id(register_id=register.id)
        return render_template('register/form.html', register=register, payments=payments)
    
@register_bp.route('/delete')
def delete_register():
    # delete_all_record()
    return redirect(url_for('room.list_rooms'))