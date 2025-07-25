import requests
from flask import Flask, redirect, url_for, request,render_template, send_file
from .routes.api import api
from .util import *

app = Flask(__name__)


@app.route('/')
def home_page():
    floors = floor_wise()
    return render_template('index.html', floors = floors)

@app.route('/inventory')
def inventory_page():
    return render_template('inventory.html')

@app.route('/report', methods=['POST', 'GET'])
def report_page():
    if request.method == 'POST':
        generate_report(request.form.get('date'))
        return send_file(TEMP_DOCX, download_name=f'{request.form.get('date')}.docx')
    return render_template('report.html')

@app.route('/account', methods=['POST', 'GET'])
def account_page():
    if request.method == 'POST':
        if request.form.get('room') == 'Credit':
            add_data(TRANSACTION_DB, ['-1', datetime.now().strftime('%Y-%m-%dT%H:%M'), request.form.get('amount'), request.form.get('mode'), request.form.get('description')])
            return redirect(url_for('home_page'))
        query = search_query(REGISTER_DB, f'checkout==\'\' and room==\'{request.form.get('room')}\'')
        if len(query)==0:
            return redirect(url_for('account_page'))
        register_id = query[0]['id']
        add_data(TRANSACTION_DB, [register_id, datetime.now().strftime('%Y-%m-%dT%H:%M'), request.form.get('amount'), request.form.get('mode'), request.form.get('description')])
        return redirect(url_for('home_page'))
    payments = payment_info()
    context = {
        'overall_total': total_balance(''),
        'total_cash_available': total_balance('Cash'),
        'payments': payments,
        'rooms': get_rooms()
    }
    return render_template('account.html', **context)

@app.route('/room/<room_no>', methods = ['POST', 'GET'])
def go_to_room(room_no):
    query2 = search_query(ROOMS_DB, f'Room_No_==\'{room_no}\'')
    if request.method == 'POST':
        # Add Data to db
        
        query = search_query(CUSTOMER_DB, f'Id_Type == \"{request.form.get("id_type", "").lower()}\" and Id_Detail.str.contains(\"{request.form.get("id_detail", "").lower()}\")')
        if len(query) == 0:
            customer_id = get_next_id(CUSTOMER_DB)
            add_data(CUSTOMER_DB, [customer_id, request.form.get('name'), str(request.form.get('address')).replace(',', '|'), request.form.get('phone'), request.form.get('id_type', '').lower(), request.form.get('id_detail', '').lower()])
        else:
            customer_id = query[0]['id']
        query3 = search_query(REGISTER_DB, f'room == \'{room_no}\' and checkout == \'\'')
        if len(query3) == 0:
            register_id = get_next_id(REGISTER_DB)
        else:
            register_id = query3[0]['id']
        data = [int(register_id), int(customer_id), int(room_no), request.form.get('ac'), request.form.get('checkin'), request.form.get('checkout'), int(request.form.get('rpd', '0'))]
        if query2[0]['Status']=='1':
            discord_post(json={'embeds': [{'description': f'Name: {request.form.get("name")}\nPhone No.: {request.form.get("phone")}\nAddress: {request.form.get("address")}', 'title': f"Check In Room No.: {room_no}"}]})
            add_data(REGISTER_DB, data)
        else:
            update_data(REGISTER_DB, f'checkout == \'\' and room == {room_no}', data)
        if request.form.get('checkout', '') == '':
            update_room(int(room_no), 2)
        else:
            discord_post(json={'embeds': [{'description': f'Name: {request.form.get("name")}\nPhone No.: {request.form.get("phone")}\nAddress: {request.form.get("address")}', 'title': f"Check Out Room No.: {room_no}"}]})
            update_checkout(int(room_no), request.form.get('checkout'))
            update_room(room_no, 1)
        return redirect(url_for('home_page'))
    formData = get_room_details(int(room_no))
    checkin = formData.get('check_in', '')
    time_passed = None
    amount_paid = None
    if checkin != '':
        time_passed = (datetime.now(ZoneInfo('Asia/Kolkata')).replace(tzinfo=None) - datetime.strptime(checkin, "%Y-%m-%dT%H:%M"))
        time_passed = f"{time_passed.days} Days {time_passed.seconds // (60 * 60)} Hours"
        amount_paid = get_amount_paid(formData['id'])
    return render_template('form.html', room_no = room_no, formData = formData, time_passed=time_passed, amount_paid=amount_paid)

app.register_blueprint(api, url_prefix='/api')