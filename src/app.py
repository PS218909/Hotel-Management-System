import requests
from flask import Flask, redirect, url_for, request, render_template, send_file
from flask_cors import CORS
from .routes.api import api
from .util import *

app = Flask(__name__)
CORS(app, resources={'/api/*': {'origins': '*'}})

@app.route('/')
def home_page():
    upload_pending()
    floors = floor_wise()
    return render_template('index.html', floors = floors)

@app.route('/inventory')
def inventory_page():
    return render_template('inventory.html')

@app.route('/report', methods=['POST', 'GET'])
def report_page():
    if request.method == 'POST':
        generate_report(request.form.get('date'))
        return send_file(TEMP_DOCX, download_name=str(request.form.get('date', '1-Jan-2025')) + '.docx')
    print(date_by_info())
    return render_template('report.html', datas = date_by_info())

@app.route('/account', methods=['POST', 'GET'])
def account_page():
    if request.method == 'POST':
        if request.form.get('room') == 'Credit':
            add_data(TRANSACTION_DB, ['-1', datetime.now().strftime('%Y-%m-%dT%H:%M'), str(request.form.get('amount')), str(request.form.get('mode')), str(request.form.get('description'))])
            return redirect(url_for('home_page'))
        query = search_query(REGISTER_DB, "checkout==\'\' and room==\'" + str(request.form.get('room')) + '\'')
        print(str(request.form))
        print(query, "Heii I am QUery Res")
        if len(query) == 0:
            return redirect(url_for('account_page'))
        register_id = query[0]['id']
        add_data(TRANSACTION_DB, [register_id, datetime.now().strftime('%Y-%m-%dT%H:%M'), str(request.form.get('amount')), str(request.form.get('mode')), str(request.form.get('description'))])
        return redirect(url_for('home_page'))
    payments = payment_info()
    context = {
        'overall_total': total_balance(''),
        'total_cash_available': total_balance('Cash'),
        'payments': payments[::-1],
        'rooms': get_rooms()
    }
    return render_template('account.html', **context)

@app.route('/room/<room_no>', methods = ['POST', 'GET'])
def go_to_room(room_no):
    query2 = search_query(ROOMS_DB, 'Room_No_==\'' + room_no + '\'')
    if request.method == 'POST':
        # Add Data to db
        query = search_query(CUSTOMER_DB, 'Id_Type.str.lower().str.contains(\"' + str(request.form.get("id_type", "")) + '\") and Id_Detail.str.lower().str.contains(\"' + str(request.form.get("id_detail", "").lower()) + '\")')
        query = search_customer_(id_type=request.form.get('id_type', ''), id_details=request.form.get('id_detail', ''))
        if len(query) == 0:
            customer_id = get_next_id(CUSTOMER_DB)
            add_data(CUSTOMER_DB, [customer_id, str(request.form.get('name')), str(request.form.get('address')).replace(',', '|'), str(request.form.get('phone')), str(request.form.get('id_type', '')), str(request.form.get('id_detail', ''))])
        else:
            customer_id = query[0]['id']
        query3 = search_query(REGISTER_DB, 'room == \'' + room_no + '\' and checkout == \'\'')
        if len(query3) == 0:
            register_id = get_next_id(REGISTER_DB)
        else:
            register_id = query3[0]['id']
        data = [int(register_id), int(customer_id), str(request.form.get('pov')), int(room_no), str(request.form.get('ac')), str(request.form.get('checkin')), str(request.form.get('checkout', '')), int(request.form.get('rpd', '0'))]
        if query2[0]['Status'] == '1':
            discord_post(json={'embeds': [{'description': 'Name: ' + str(request.form.get('name')) + '\nPhone No.: ' + str(request.form.get('phone')) + '\nAddress: ' + str(request.form.get('address')) + '\nCheckin Time: ' + str(request.form.get('checkin')), 'title': 'Check In Room No.: ' + room_no}]})
            add_data(REGISTER_DB, data)
        else:
            update_data(REGISTER_DB, 'checkout == \'\' and room == ' + room_no, data)
        if request.form.get('checkout', '') == '':
            update_room(int(room_no), 2)
        else:
            discord_post(json={'embeds': [{'description': 'Name: ' + str(request.form.get('name')) + '\nPhone No.: ' + str(request.form.get('phone')) + '\nAddress: ' + str(request.form.get('address')) + '\nCheckout Time: ' + str(request.form.get('checkout')), 'title': 'Check Out Room No.: ' + room_no}]})
            update_checkout(int(room_no), request.form.get('checkout'))
            update_room(room_no, 1)
        return redirect(url_for('home_page'))
    formData = get_room_details(int(room_no))
    checkin = formData.get('check_in', '')
    time_passed = None
    amount_paid = None
    available_rooms = None
    payment_list = None
    if checkin != '':
        time_passed = (datetime.now(ZoneInfo('Asia/Kolkata')).replace(tzinfo=None) - datetime.strptime(checkin, "%Y-%m-%dT%H:%M"))
        time_passed = str(time_passed.days) + " Days " + str(time_passed.seconds // (60 * 60)) + " Hours"
        amount_paid, payment_list = get_amount_paid(formData['id'])
        available_rooms = search_query(ROOMS_DB, 'Status == \'1\'')
    return render_template('form.html', room_no = room_no, formData = formData, time_passed = time_passed, amount_paid = amount_paid, available_rooms=available_rooms, payment_list=payment_list)

@app.route('/register')
def go_to_register():
    page = int(request.args.get('page', 0))
    return render_template('register.html', register_entries=get_info_register(page), page=page)

@app.route('/shift', methods=['POST'])
def shift_post():
    shift_rooms(int(request.form.get('from_', '0')), int(request.form.get('to', '0')))
    return redirect(url_for('home_page'))

app.register_blueprint(api, url_prefix='/api')
