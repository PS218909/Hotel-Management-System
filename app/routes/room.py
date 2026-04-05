from flask import Blueprint, request, jsonify, redirect, url_for, render_template, flash
from app.services.room import get_room_by_id, alter_room, get_all_rooms, create_room, find_room, get_available_rooms, delete_room
from app.services.register import create_register, alter_register, get_registers_by_room, get_register_by_current_stay
from app.services.transaction import get_transaction_by_register_id
from app.util.helper import calculate_time_difference, calculate_total_balance, send_webhook_alert
from datetime import datetime
from typing import Any

room_bp = Blueprint('room', __name__, url_prefix='/room')

@room_bp.route('/')
def list_rooms():
    # Logic to list all rooms
    rooms = get_all_rooms()
    for room in rooms:
        if not room.is_available:
            try:
                register_info = get_registers_by_room(room.id)[-1]
            except Exception as err:
                continue
            room.time_passed = calculate_time_difference(register_info.check_in, return_str=True)
            room.name = register_info.customer.name
            room.phone = register_info.customer.phone
            room.ac = register_info.ac
    return render_template('room/index.html', rooms=rooms)

@room_bp.route('/<int:room_no>', methods=['GET', 'POST'])
def form_room(room_no):
    room = find_room(room_number=room_no)
    if room:
        room = room[0]
    else:
        flash('Room not found', 'error')
        return redirect(url_for('room.list_rooms'))
    if request.method == 'POST':
        data: dict[str, Any] = dict(request.form)
        data.update({
            'check_out': datetime.strptime(data.get('check_out', ''), '%Y-%m-%dT%H:%M') if data.get('check_out', None) else None,
            'check_in': datetime.strptime(data.get('check_in', datetime.now().strftime('%Y-%m-%dT%H:%M')), '%Y-%m-%dT%H:%M'),
            'ac': True if data.get('ac') == 'true' else False, 
        })
        data.update({
            'customer_id_2': data.get('customer_id_2', None),
            'customer_id_3': data.get('customer_id_3', None),
            'customer_id_4': data.get('customer_id_4', None),
            'customer_id_5': data.get('customer_id_5', None),
            'customer_id_6': data.get('customer_id_6', None),
            'customer_id_7': data.get('customer_id_7', None),
            'customer_id_8': data.get('customer_id_8', None),
            'customer_id_9': data.get('customer_id_9', None),
            'customer_id_10': data.get('customer_id_10', None),
            'customer_id_11': data.get('customer_id_11', None),
            'customer_id_12': data.get('customer_id_12', None),
        })
        if room.is_available:
            alter_room(room.id, is_available=False)
            register = create_register(**data)
            if register:
                create_dict = {
                    'Room No.': register.room.room_number,
                    'Name': register.customer.name,
                    'Address': register.customer.address,
                    'Phone': register.customer.phone,
                    'Check In': register.check_in.strftime('%d-%m-%Y %H:%M'),
                    'Check Out': register.check_out.strftime('%d-%m-%Y %H:%M') if register.check_out else '',
                }
                send_webhook_alert({
                    'title': '✅ Check In' + str(register.room.room_number), 
                    'description': '\n'.join('**'+str(k)+': **'+str(v) for k, v in create_dict.items()),
                })
        else:
            if data.get('check_out'):
                alter_room(room.id, is_available=True)
                register = alter_register(**data)
                if register:
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
                        'title': '🕛 Check Out ' + str(register.room.room_number), 
                        'description': '\n'.join('**'+str(k)+': **'+str(v) for k, v in alert_dict.items()),
                    })
            register = get_register_by_current_stay(room.id)
            if register:
                alter_register(register.id, **data)
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
                    'title': '✏️ Update Details ' + str(register.room.room_number), 
                    'description': '\n'.join('**'+str(k)+': **'+str(v) for k, v in alert_dict.items()),
                })
        flash('Room details updated successfully', 'success')
        return redirect(url_for('room.list_rooms'))
    # Logic to display a specific room's details
    register = get_register_by_current_stay(room.id)
    payments = []
    empty_rooms = []
    if register:
        tp = calculate_time_difference(register.check_in)
        register.time_passed = f'{tp[0]} Days {round(tp[1], 1)} Hours' # type: ignore
        register.total_amount = calculate_total_balance(register.rent_per_day, register.check_in)
        register.remaining_balance = calculate_total_balance(register.rent_per_day, register.check_in) - register.total_paid
        payments = get_transaction_by_register_id(register_id=register.id)
        empty_rooms = get_available_rooms()
    return render_template('room/form.html', register=register, room = room, payments=payments, empty_rooms=empty_rooms)

@room_bp.route('/shift', methods=['POST'])
def room_shift():
    data = request.form
    alter_room(room_id=data['room_id'], is_available=False)
    alter_room(room_id=data['old_room_id'], is_available=True)
    register = alter_register(**data)
    if register:
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
            'title': '🔁 Shift from **' + str(get_room_by_id(room_id=data['old_room_id']).room_number) + '** to **' + register.room.room_number + '**', 
            'description': '\n'.join('**'+str(k)+': **'+str(v) for k, v in alert_dict.items()),
        })
    return redirect('/')

@room_bp.route('/edit/<int:id>', methods=['POST'])
def _edit_room_details(id):
    data = request.form
    alter_room(room_id=id, **data)
    return redirect(request.referrer)

@room_bp.route('/delete', methods=['POST'])
def _delete_room():
    data = request.form
    if delete_room(int(data.get('room_id', -1))):
        flash('Room Deleted Successfully.')
    else:
        flash('Something went wrong.')
    return redirect(request.referrer)

@room_bp.route('/create', methods=['POST'])
def create_room_page():
    # Logic to create a new room
    data = request.form
    room = create_room(**data) # type: ignore
    if room:
        flash('Room created successfully!', 'success')
        return redirect(request.referrer)
    return jsonify({"message": "Failed to create room"}), 400