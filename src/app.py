from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, abort
from .util import *
from .analysis import get_analysis
from datetime import datetime, timedelta
from functools import wraps

def encrypt(key):
    hashed = ''
    for idx, i in enumerate(list(key)):
        hashed += chr(ord(i) + (-1 ** (idx)) * idx)
    return hashed

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'uname' not in session:
                return redirect(url_for('login_page'))
            user_role = session.get('urole', 'staff')
            if user_role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

app = Flask(__name__)
app.secret_key = "HEHE LOL I AM NULL"
app.permanent_session_lifetime = timedelta(minutes=720) 

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        df = read_csv(USERS_DB)
        uname = request.form.get('username', '')
        pwd = request.form.get('password', '')
        df = df[df['username'] == uname]
        if len(df) == 0:
            flash("User not found", 'danger')
            return redirect(url_for('login_page'))
        if df.loc[0, 'password'] != encrypt(pwd):
            flash('Invalid password', 'danger')
            return redirect(url_for('login_page'))
        session.setdefault('uname', request.form.get('username'))
        session.setdefault('urole', df.loc[0, 'role'])
        append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'login','','',uname])
        return redirect(url_for('index_page'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        uname = request.form.get('username', '')
        pwd = request.form.get('password', '')
        # Input Validation
        if len(uname) < 3:
            flash('Username should have more than 2 characters', 'danger')
            return redirect(url_for('signup_page'))
        symbol = True
        digits = 2
        uppercase = True
        lowercase = True
        for i in pwd:
            if i in '!@#$%^&*()_+=-`~|\\{[]}\'";:/?.>,<':
                symbol = False
            if i.isdigit():
                digits -= 1
            if i.isupper():
                uppercase = False
            if i.islower():
                lowercase = False
        if len(pwd) < 8 or symbol or uppercase or lowercase or digits > 0:
            flash('Password should contain more than 8 characters.\n* 2 Digits\n* 1 Symbol \n* Both uppercase and lowercase character', 'danger')
            return redirect(url_for('signup_page'))
        df = read_csv(USERS_DB)
        if len(df[df['username'].str.lower() == uname.lower()]) > 0:
            flash('User Already Exists', 'danger')
            return redirect(url_for('signup_page'))
        append_row(USERS_DB, [uname.lower(), encrypt(pwd), 'staff'])
        append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'signup','','',uname])
        return redirect(url_for('index_page'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'logout','','',session.get('uname', 'huh')])
    session.pop('uname')
    session.pop('urole')
    return redirect(url_for('index_page'))

@app.route('/')
def index_page():
    push_webhook_alerts()
    stats = get_rooms_status()
    return render_template("index.html", stats = stats, login=session.get('uname', None))

@app.route('/room/<rno>', methods=['GET', 'POST'])
@roles_required('admin', 'manager')
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
            append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'create:customer','','',session.get('uname', 'huh')])
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
            append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'checkin','',rno,session.get('uname', 'huh')])
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
                append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'checkout',rno,'',session.get('uname', 'huh')])
                update_row(ROOMS_DB, {'r': rno}, {'s': 1})
            return redirect(url_for('index_page'))
    context = get_room_detail(rno)['data']
    empty_rooms = find_by({'s': 1}, ROOMS_DB).to_dict(orient='records')
    return render_template("roomForm.html", **context, empty_room=empty_rooms, login=session.get('uname', None))

@app.route('/account', methods=['GET'])
@roles_required('admin', 'manager')
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
        return render_template('account.html', rooms=occupied_rooms, payments=payments, **today, login=session.get('uname', None))
    else:
        return jsonify({'success': False, 'message': 'Method not allowed.'})

@app.route('/register', methods=['GET'])
@roles_required('admin', 'manager', 'staff')
def register_page():
    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 50))
    cid = int(request.args.get('cid', 0))
    if cid == 0:
        cid = None
    else:
        count = 10000
    if page < 1:
        page = 1
        return redirect(url_for('register_page', page=page, count=count, cid=cid))
    register = get_register_detail(page=page, count=count, cid=cid).to_dict(orient='records')
    if len(register) == 0:
        page = len(read_csv(REGISTER_DB))//count
        return redirect(url_for('register_page', page=page + 1, count=count, cid=cid))
    return render_template('register.html', register = register, count=count, login=session.get('uname', None))

@app.route('/report', methods=['GET'])
@roles_required('admin', 'manager', 'staff')
def report_page():
    month_arg = request.args.get('month', str(datetime.now().year) + '-' + str(datetime.now().month))
    year, month = month_arg.split('-')
    records = get_report_records(month=month, year=year)
    return render_template('report.html', records = records, month=year+'-'+month, date=datetime.today().strftime("%Y-%m-%d"), login=session.get('uname', None))

@app.route('/analysis', methods=['GET', 'POST'])
@roles_required('admin')
def analysis_page():
    start_time, end_time = None, None
    if request.method == 'POST':
        start_time = request.form.get('start', None)
        end_time = request.form.get('end', None)
    context = get_analysis(start_time, end_time, all=True)
    return render_template('analysis.html', login=session.get('uname', None), **context) # type: ignore

@app.route('/customers')
@roles_required('admin', 'manager', 'staff')
def customer_page():
    customers = read_csv(CUSTOMERS_DB)
    return render_template('customer.html', customers=customers.to_dict(orient='records'), login=session.get('uname', None))

@app.route('/gst', methods=['GET'])
@roles_required('admin')
def gst_page():
    gst_detail = fetch_gst_info()
    return render_template('gst.html', register=gst_detail.to_dict(orient='records'), login=session.get('uname', None))


@app.route('/customer/update', methods=['POST'])
@roles_required('admin', 'manager')
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
    append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'customer:update','','',session.get('uname', 'huh')])
    flash('Customer Details Updated Successfully.', 'success')
    return redirect(url_for('customer_page'))


@app.route('/transaction', methods=['POST'])
@roles_required('admin', 'manager', 'staff')
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
            append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'transaction:add','','',session.get('uname', 'huh')])
            flash(request.form.get('amount', '0') + ' Rupee received through ' + request.form.get('mode', 'Unknown') + '.', 'success')
            return redirect(url_for('index_page'))
        else:
            flash('Something went wrong. Please try again.', 'danger')
            return redirect(url_for('room_form_page', rno=request.form.get('roomno')))
    else:
        return jsonify({'success': False, 'message': 'Method not allowed'})

@app.route('/transaction/id', methods=['POST'])
@roles_required('admin', 'manager', 'staff')
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
        append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'transaction:add_register','','',session.get('uname', 'huh')])
        flash(request.form.get('amount', '0') + ' Rupee received through ' + request.form.get('mode', 'Unknown') + '.', 'success')
        return redirect(url_for('register_page'))
    else:
        flash('Something went wrong. Maybe invalid user input.', 'danger')
        return redirect(url_for('index_page'))

@app.route('/transaction/update', methods=['POST'])
@roles_required('admin', 'manager')
def update_transaction():
    if request.method == 'POST':
        prev_time = request.form.get('time')
        days, hours = time_difference(prev_time)
        if session.get('urole') == 'manager' and (days > 0 or hours > 1):
            flash('Payment cannot be updated after 1 hours', 'danger')
            return redirect(url_for('account_page'))
        res = update_row(TRANSACTIONS_DB, {'id': request.form.get('id')}, {'a': int(request.form.get('amount', '0')), 'm': request.form.get('mode'), 'd': request.form.get('description')})
        append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'transaction:update','','',session.get('uname', 'huh')])
        if res['success']:
            send_webhook_alert({'title': '💱 Update Payment ' + str(request.form.get('roomno', '')), 'description': '**Amount: **' + str(request.form.get('amount', '')) + '\n**Mode: **' + str(request.form.get('mode', '')) + '\n**Description: **' + str(request.form.get('description', ''))})
            flash('Payment Updated Successfully', 'success')
        else:
            flash('Unable to update payment because ' + res['message'], 'danger')
        return redirect(url_for('account_page'))
    else:
        return {'success': False, 'message': 'method not allowed'}

@app.route('/transaction/delete', methods=['POST'])
@roles_required('admin', 'manager')
def delete_transaction():
    if request.method == 'POST':
        prev_time = request.form.get('time')
        days, hours = time_difference(prev_time)
        if session.get('urole') == 'manager' and days > 0 or hours > 1:
            flash('Payment cannot be deleted after 1 hours', 'danger')
            return redirect(url_for('account_page'))
        res = delete_row(TRANSACTIONS_DB, {'id': request.form.get('id')})
        append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'transaction:delete','','',session.get('uname', 'huh')])
        if res['success']:
            send_webhook_alert({'title': '❌ Delete Payment ' + str(request.form.get('roomno', '')), 'description': '**Amount: **' + str(request.form.get('amount', '')) + '\n**Mode: **' + str(request.form.get('mode', '')) + '\n**Description: **' + str(request.form.get('description', '')), 'color': 0xff0000})
            flash('Payment Deleted Successfully', 'success')
        else:
            flash('Unable to delete payment because ' + res['message'], 'danger')
        return redirect(url_for('account_page'))
    else:
        return {'success': False, 'message': 'method not allowed'}

@app.route('/shift', methods=['POST'])
@roles_required('admin', 'manager')
def shift_room():
    if request.method == 'POST':
        nroom = request.form.get('nroom', '')
        room = request.form.get('room', '')
        if room != '' and nroom != '':
            update_row(REGISTER_DB, {'rno': int(room), 'cout': ''}, {'rno': nroom})
            update_row(ROOMS_DB, {'r': room}, {'s': 1})
            update_row(ROOMS_DB, {'r': nroom}, {'s': 2})
            append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'shift',room,nroom,session.get('uname', 'huh')])
            send_webhook_alert({'title': '🔄 Shifting from **' + room + '** to **' + nroom + '**', 'description': '', 'color': 0x0000ff})
            flash('Shifting from ' + room + ' to ' + nroom + 'Successfully.', category='success')
            return redirect(url_for('index_page'))
        else:
            flash('Shifting from ' + room + ' to ' + nroom + ' Failed.', category='danger')
            return redirect(url_for('room_form_page', rno=room))
    else:
        return jsonify({'success': False, 'message': 'Method not allowed'})

@app.route('/update/gst_detail', methods=['POST'])
@roles_required('admin', 'manager')
def update_gst_detail():
    rid = request.form.get('id')
    gb = request.form.get('gst_bill')
    update_row(REGISTER_DB, {'id': rid}, {'gb': gb})
    append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'add_gst_detail','','',session.get('uname', 'huh')])
    return redirect(url_for('register_page'))

@app.route('/generate', methods=['GET'])
@roles_required('admin', 'manager', 'staff')
def generate_report():
    date = request.args.get('date')
    filepath = create_report(date)
    flash('\"' + filepath + '\" saved successfully', 'success')
    append_row(EVENT_LOG, [datetime.now().strftime('%d-%m-%Y %H:%M:%S'),'generate:report','','',session.get('uname', 'huh')])
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