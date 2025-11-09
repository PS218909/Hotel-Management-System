from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from .util import *
from .analysis import get_analysis
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "HEHE LOL I AM NULL"

@app.route('/')
def index_page():
    push_webhook_alerts()
    stats = get_rooms_status()
    return render_template("index.html", stats = stats)

@app.route('/room/<rno>', methods=['GET', 'POST'])
def room_form_page(rno):
    if request.method == 'POST':
        query = find_by({'it': request.form.get('id_type', ''), 'ip': request.form.get('id_detail', '')}, CUSTOMERS_DB)
        if len(query) > 0:
            customer_id = query.iloc[0]['id']
        else:
            customer_id = next_id(CUSTOMERS_DB)
            append_row(CUSTOMERS_DB, [
                customer_id, 
                request.form.get('name'), 
                request.form.get('address'), 
                request.form.get('phone'), 
                request.form.get('id_type'), 
                request.form.get('id_detail')
            ])
        if len(find_by({'r': rno, 's': 1}, ROOMS_DB)) > 0:
            send_webhook_alert({
                'title': '✅ Check In '+ str(rno), 
                'description': '**Name: **'+ str(request.form.get('name', '')) +'\n**Address: **'+ str(request.form.get('address', '')) + '\n**Phone: **' + str(request.form.get('phone', '')) + '**\nCheck In: **' + transform_time(request.form.get('checkin', '2025-01-01T00:00')), # type: ignore
                'color': 0x00ff00
            })
            append_row(REGISTER_DB, [
                next_id(REGISTER_DB), 
                rno, 
                customer_id, 
                request.form.get('ac', 'NON_AC'), 
                request.form.get('rpd', 0), 
                request.form.get('pov'), 
                request.form.get('checkin'), 
                '',
                ''
            ])
            update_row(ROOMS_DB, {'r': rno}, {'r': rno, 's': 2})
            return redirect(url_for('index_page'))
        else:
            rid = find_by({'rno': rno, 'cout': None}, REGISTER_DB)
            rid = rid.loc[rid.index[0], 'id']
            amount_paid = fetch_payments(rid=rid, get_sum=True)
            update_row(REGISTER_DB, {'rno': rno, 'cout': ''}, {'cid': customer_id, 'ac': request.form.get('ac'), 'rpd': str(request.form.get('rpd')), 'pov': request.form.get('pov'), 'cin': request.form.get('checkin'), 'cout': request.form.get('checkout', ''), 'gb': request.form.get('gst_bill', '')})
            if request.form.get('checkout', '') != '':
                send_webhook_alert({
                    'title': '🕛 Check Out '+ str(rno), 
                    'description': '**Name: **'+ str(request.form.get('name', '')) +'\n**Address: **'+ str(request.form.get('address', '')) + '\n**Phone: **' + str(request.form.get('phone', '')) + '**\nCheck In: **' + transform_time(request.form.get('checkin', '2025-01-01T00:00')) + '**\nCheck Out: **' + transform_time(request.form.get('checkout', '2025-01-01T00:00')) + '**\nAmount Paid: **' + str(amount_paid), # type: ignore
                    'color': 0xff0000
                })
                update_row(ROOMS_DB, {'r': rno}, {'s': 1})
            return redirect(url_for('index_page'))
    context = get_room_detail(rno)['data']
    empty_rooms = find_by({'s': 1}, ROOMS_DB).to_dict(orient='records')
    return render_template("roomForm.html", **context, empty_room=empty_rooms)

@app.route('/account', methods=['GET'])
def account_page():
    if request.method == 'GET':
        occupied_rooms = find_by({'s': 2}, ROOMS_DB).to_dict(orient='records')
        page = int(request.args.get('page', 1)) - 1
        count = int(request.args.get('count', 50))
        payments = fetch_payments(page=page, count=count)
        today_payments = fetch_payments(date=datetime.now().strftime('%Y-%m-%d'))
        if len(payments) == 0:
            return redirect(url_for('account_page', page=page, count=count))
        today = {'total_amount': 0, 'cash': 0, 'upi': 0}
        for row in today_payments:
            mode = row['m'].lower().strip() # type: ignore
            amount = row['a_x'] if row['rid'] != -1 else -row['a_x'] # type: ignore
            if mode in ['cahs', 'cash', 'csah', 'chsa'] or mode.startswith('c'):
                today['cash'] += amount # type: ignore
                today['total_amount'] += amount # type: ignore
            elif mode in ['upi', 'uip', 'ipu'] or mode.startswith('u'):
                today['upi'] += amount # type: ignore
                today['total_amount'] += amount # type: ignore
        return render_template('account.html', rooms=occupied_rooms, payments=payments, **today)
    else:
        return jsonify({'success': False, 'message': 'Method not allowed.'})

@app.route('/register', methods=['GET'])
def register_page():
    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 50))
    if page < 1:
        page = 1
        return redirect(url_for('register_page', page=page, count=count))
    register = get_register_detail(page=page, count=count).to_dict(orient='records')
    if len(register) == 0:
        page = len(read_csv(REGISTER_DB))//count
        return redirect(url_for('register_page', page=page + 1, count=count))
    return render_template('register.html', register = register, count=count)

@app.route('/report', methods=['GET'])
def report_page():
    month_arg = request.args.get('month', str(datetime.now().year) + '-' + str(datetime.now().month))
    year, month = month_arg.split('-')
    records = get_report_records(month=month, year=year)
    return render_template('report.html', records = records, month=year+'-'+month, date=datetime.today().strftime("%Y-%m-%d"))

@app.route('/analysis', methods=['GET', 'POST'])
def analysis_page():
    start_time, end_time = None, None
    if request.method == 'POST':
        start_time = request.form.get('start', None)
        end_time = request.form.get('end', None)
    context = get_analysis(start_time, end_time, all=True)
    return render_template('analysis.html', **context) # type: ignore

@app.route('/customers')
def customer_page():
    customers = read_csv(CUSTOMERS_DB)
    return render_template('customer.html', customers=customers.to_dict(orient='records'))

@app.route('/gst', methods=['GET'])
def gst_page():
    gst_detail = fetch_gst_info()
    return render_template('gst.html', register=gst_detail.to_dict(orient='records'))


@app.route('/customer/update', methods=['POST'])
def update_customer():
    cid, name, phone, address, id_type, id_detail = request.form.get('id', ''), request.form.get('name', ''), request.form.get('phone', ''), request.form.get('address', ''), request.form.get('id_type', ''), request.form.get('id_detail', '')
    update_row(
        CUSTOMERS_DB, 
        {
            'id': cid
        }, 
        {
            'n': name, 
            'p': phone, 
            'a': address, 
            'it': id_type, 
            'ip': id_detail
        }
    )
    flash('Customer Details Updated Successfully.', 'success')
    return redirect(url_for('customer_page'))


@app.route('/transaction', methods=['POST'])
def add_transaction():
    if request.method == 'POST':
        if request.form.get('amount') != '' and request.form.get('mode') != '':
            rid = find_by({'rno': request.form.get('roomno'), 'cout': None}, REGISTER_DB)
            send_webhook_alert({
                'title': '💰 Add Payment ' + str(request.form.get('roomno', '')), 
                'description': '**Amount: **' + str(request.form.get('amount', '')) + '\n**Mode: **' + str(request.form.get('mode', '')) + '\n**Description: **' + str(request.form.get('description', '')), 
                'color': 0x0f0fff
            })
            append_row(TRANSACTIONS_DB, [
                next_id(TRANSACTIONS_DB), 
                rid.loc[rid.index[0], 'id'] if request.form.get('roomno') != '-1' else -1, 
                request.form.get('amount', 0), 
                request.form.get('time', datetime.now().strftime("%Y-%m-%dT%H:%M")), 
                request.form.get('mode', 'cash'), 
                request.form.get('description', '')
            ])
            flash(request.form.get('amount', '0') + ' Rupee received through ' + request.form.get('mode', 'Unknown') + '.', 'success')
            return redirect(url_for('index_page'))
        else:
            flash('Something went wrong. Please try again.', 'danger')
            return redirect(url_for('room_form_page', rno=request.form.get('roomno')))
    else:
        return jsonify({'success': False, 'message': 'Method not allowed'})

@app.route('/transaction/id', methods=['POST'])
def add_transaction_id():
    if request.form.get('amount', '') != '' and request.form.get('mode', '') != '' and request.form.get('id', ''):
        append_row(TRANSACTIONS_DB, [
            next_id(TRANSACTIONS_DB),
            request.form.get('id', ''),
            request.form.get('amount', 0),
            request.form.get('time', datetime.now().strftime("%Y-%m-%dT%H:%M")),
            request.form.get('mode', 'cash'),
            request.form.get('description', '')
        ])
        flash(request.form.get('amount', '0') + ' Rupee received through ' + request.form.get('mode', 'Unknown') + '.', 'success')
        return redirect(url_for('register_page'))
    else:
        flash('Something went wrong. Maybe invalid user input.', 'danger')
        return redirect(url_for('index_page'))

@app.route('/transaction/update', methods=['POST'])
def update_transaction():
    if request.method == 'POST':
        prev_time = request.form.get('time')
        days, hours = time_difference(prev_time)
        if days > 0 or hours > 1:
            flash('Payment cannot be updated after 1 hours', 'danger')
            return redirect(url_for('account_page'))
        res = update_row(TRANSACTIONS_DB, {'id': request.form.get('id')}, {'a': int(request.form.get('amount', '0')), 'm': request.form.get('mode'), 'd': request.form.get('description')})
        if res['success']:
            send_webhook_alert({'title': '💱 Update Payment ' + str(request.form.get('roomno', '')), 'description': '**Amount: **' + str(request.form.get('amount', '')) + '\n**Mode: **' + str(request.form.get('mode', '')) + '\n**Description: **' + str(request.form.get('description', ''))})
            flash('Payment Updated Successfully', 'success')
        else:
            flash('Unable to update payment because ' + res['message'], 'danger')
        return redirect(url_for('account_page'))
    else:
        return {'success': False, 'message': 'method not allowed'}

@app.route('/transaction/delete', methods=['POST'])
def delete_transaction():
    if request.method == 'POST':
        prev_time = request.form.get('time')
        days, hours = time_difference(prev_time)
        if days > 0 or hours > 1:
            flash('Payment cannot be deleted after 1 hours', 'danger')
            return redirect(url_for('account_page'))
        res = delete_row(TRANSACTIONS_DB, {'id': request.form.get('id')})
        if res['success']:
            send_webhook_alert({'title': '❌ Delete Payment ' + str(request.form.get('roomno', '')), 'description': '**Amount: **' + str(request.form.get('amount', '')) + '\n**Mode: **' + str(request.form.get('mode', '')) + '\n**Description: **' + str(request.form.get('description', '')), 'color': 0xff0000})
            flash('Payment Deleted Successfully', 'success')
        else:
            flash('Unable to delete payment because ' + res['message'], 'danger')
        return redirect(url_for('account_page'))
    else:
        return {'success': False, 'message': 'method not allowed'}

@app.route('/shift', methods=['POST'])
def shift_room():
    if request.method == 'POST':
        nroom = request.form.get('nroom', '')
        room = request.form.get('room', '')
        if room != '' and nroom != '':
            update_row(REGISTER_DB, {'rno': int(room), 'cout': ''}, {'rno': nroom})
            update_row(ROOMS_DB, {'r': room}, {'s': 1})
            update_row(ROOMS_DB, {'r': nroom}, {'s': 2})
            send_webhook_alert({'title': '🔄 Shifting from **' + room + '** to **' + nroom + '**', 'description': '', 'color': 0x0000ff})
            flash('Shifting from ' + room + ' to ' + nroom + 'Successfully.', category='success')
            return redirect(url_for('index_page'))
        else:
            flash('Shifting from ' + room + ' to ' + nroom + ' Failed.', category='danger')
            return redirect(url_for('room_form_page', rno=room))
    else:
        return jsonify({'success': False, 'message': 'Method not allowed'})

@app.route('/update/gst_detail', methods=['POST'])
def update_gst_detail():
    rid = request.form.get('id')
    gb = request.form.get('gst_bill')
    update_row(REGISTER_DB, {'id': rid}, {'gb': gb})
    return redirect(url_for('register_page'))

@app.route('/generate', methods=['GET'])
def generate_report():
    date = request.args.get('date')
    filepath = create_report(date)
    flash('\"' + filepath + '\" saved successfully', 'success')
    return redirect(url_for('report_page'))

@app.route('/api/sc', methods=['GET'])
def search_customer_np():
    res = search_customer(request.args.get('name', ''), request.args.get('phone', ''))
    return jsonify(res)

@app.route('/api/analysis/customer', methods=['GET'])
def analysis_customer():
    cid = request.args.get('id', None)
    if cid is None:
        return {}
    res = get_register_detail(cid=cid)
    res = res.fillna('')
    return jsonify({'tv': len(res), 'visits': res.to_dict(orient='records'), 'tap': str(res['amount_paid'].sum())})