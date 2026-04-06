from flask import Blueprint, redirect, request, render_template, url_for, current_app, send_file
import io, zipfile, pandas, time, random
from datetime import datetime
from app.models.customer import Customer
from app.models.register import Register
from app.models.room import Room
from app.models.transaction import Transaction
from app.models.user import User
from app.extensions import db
from sqlalchemy.exc import IntegrityError

from app.services.migrate import import_data, export_data

from app.util.helper import model_to_csv

migrate_bp = Blueprint('migrate', __name__, url_prefix='/migrate')

@migrate_bp.route('/')
def migrate_index():
    return render_template('migrate/index.html')

@migrate_bp.route('/import', methods=['POST', 'GET'])
def migrate_import():
    if request.method == 'POST':
        zipped = request.files['csv_data']
        buffer = io.BytesIO(zipped.read())

        # import_data(buffer)

        res = {}

        with zipfile.ZipFile(buffer, 'r') as zip:
            for name in ['rooms.csv', 'customer.csv', 'register.csv', 'transaction.csv']:
                if name.endswith('.csv'):
                    with zip.open(name) as csv:
                        decoded = io.TextIOWrapper(csv, encoding='utf-8')
                        df = pandas.read_csv(decoded)
                        if '/' in name:
                            name = name.split('/')[0]
                        if '\\' in name:
                            name = name.split('\\')[0]
                        if name.lower() in ['rooms.csv', 'room.csv']:
                            df = df.rename(columns={'r': 'room_number', 'f': 'floor_number', 's': 'is_available'})
                            df['capacity'] = 1
                            df['is_available'] = df['is_available'] == 1

                            for _, row in df.iterrows():
                                exists = db.session.query(Room).filter_by(room_number=row['room_number']).first()
                                if row['floor_number'] in ['SECOND_FLOOR', 'THIRD_FLOOR']:
                                    row['capacity'] = 2
                                if not exists:
                                    db.session.add(Room(**row.to_dict()))
                                    db.session.commit()

                            for idx, record in df.iterrows():
                                db.session.query(Room).filter(Room.room_number == record['room_number']).update({Room.is_available: record['is_available']})
                                db.session.commit()
                        if name.lower() in ['customer.csv']:
                            df = df.rename(columns={'n': 'name', 'a': 'address', 'p': 'phone', 'it': 'id_type', 'ip': 'id_detail'})
                            # df = df[['name', 'address', 'phone', 'id_type', 'id_detail']]
                            for idx, record in df.iterrows():
                                d_record = record.to_dict()
                                if record['name'] == 'ADJUST':
                                    continue
                                if record['id_type'] == '' or pandas.isna(record['id_type']):
                                    d_record['id_type'] = ' '
                                if str(record['id_detail']).strip() == '' or pandas.isna(record['id_detail']):
                                    d_record['id_detail'] = 'MISSING ' + str(random.randint(1, 1000000))
                                if record['address'] == '' or pandas.isna(record['address']):
                                    d_record['address'] = ' '
                                try:
                                    db.session.add(Customer(**d_record))
                                    db.session.commit()
                                except IntegrityError as e:
                                    db.session.rollback()
                                except Exception as err:
                                    db.session.rollback()

                        if name.lower() in ['register.csv']:
                            c_df = pandas.read_csv(zip.open('customer.csv'))
                            df = df.rename(columns={'cid': 'customer_id', 'rno': 'room_number', 'cin': 'check_in', 'cout': 'check_out', 'rpd': 'rent_per_day', 'gb': 'gst_invoice', 'pov': 'purpose_of_visit'})
                            rooms = Room.query.with_entities(Room.id, Room.room_number).all()
                            customers = Customer.query.with_entities(Customer.id, Customer.id_detail).all()
                            room_map = {int(room_number): int(room_id) for room_id, room_number in rooms}
                            customers_map = {customer_detail: customer_id for customer_id, customer_detail in customers}
                            df['room_id'] = df['room_number'].map(room_map)
                            
                            df = df[['id', 'customer_id', 'room_id', 'check_in', 'check_out', 'rent_per_day', 'gst_invoice', 'purpose_of_visit', 'ac']]
                            df['ac'] = df['ac'] == 'AC'
                            df['number_of_persons'] = 1
                            df['rent_per_day'] = df['rent_per_day'].fillna(630)
                            df['check_in'] = pandas.to_datetime(df['check_in'])
                            df['check_out'] = pandas.to_datetime(df['check_out'])
                            for idx, record in df.iterrows():
                                c_id_detail = c_df.loc[c_df['id'] == record['customer_id'], 'ip'].iloc[0]
                                if c_id_detail == 'ADJUST':
                                    continue
                                d_record = record.to_dict()
                                d_record['reg_id'] = idx+1
                                if not pandas.isna(c_id_detail):
                                    d_record['customer_id'] = customers_map[c_id_detail]
                                if (pandas.isna(record['check_out'])):
                                    del d_record['check_out']
                                try:
                                    db.session.add(Register(**d_record))
                                    db.session.commit()
                                except Exception as err:
                                    db.session.rollback()
                                    print(err)
                        
                        if name.lower() in ['transaction.csv', 'transactions.csv']:
                            df = df.rename(columns={'rid': 'register_id', 'a': 'amount_paid', 't': 'transaction_time', 'm': 'payment_method'})
                            df['transaction_time'] = pandas.to_datetime(df['transaction_time'])
                            try:
                                db.session.bulk_insert_mappings(Transaction, df.to_dict(orient='records'))
                                db.session.commit()
                            except Exception as err:
                                db.session.rollback()
                                print('[-] Transaction Error -', err)
        return redirect(url_for('register.list_registers'))

    return render_template('migrate/index.html')

@migrate_bp.route('/export', methods=['GET'])
def migrate_export():
    zip_buffer = export_data()
    # Timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'dataset_{timestamp}.zip'

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename
    )