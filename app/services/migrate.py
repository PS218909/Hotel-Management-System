from app.models.customer import Customer
from app.models.register import Register
from app.models.room import Room
from app.models.transaction import Transaction
from app.util.helper import model_to_csv
from app.extensions import db


from sqlalchemy.exc import IntegrityError
from sqlalchemy import insert
import io, zipfile, time, random
import pandas as pd

def export_data():
    customers = Customer.query.all()
    records = Register.query.all()
    rooms = Room.query.all()
    transactions = Transaction.query.all()
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('customers.csv', model_to_csv(Customer, customers))
        zf.writestr('registers.csv', model_to_csv(Register, records))
        zf.writestr('rooms.csv', model_to_csv(Room, rooms))
        zf.writestr('transactions.csv', model_to_csv(Transaction, transactions))

    zip_buffer.seek(0)
    return zip_buffer

import zipfile
import io
import pandas as pd

def import_data(zip_file):
    ref = {}

    with zipfile.ZipFile(zip_file, 'r') as z:
        # Map file names
        for name in z.namelist():
            if name.endswith('.csv'):
                if 'customer' in name:
                    ref['customer'] = name
                elif 'room' in name:
                    ref['room'] = name
                elif 'transaction' in name:
                    ref['transaction'] = name
                elif 'register' in name:
                    ref['register'] = name

        # Read CSVs directly
        customer_df = pd.read_csv(io.TextIOWrapper(z.open(ref['customer']), encoding='utf-8'))
        rooms_df = pd.read_csv(io.TextIOWrapper(z.open(ref['room']), encoding='utf-8'))
        transactions_df = pd.read_csv(io.TextIOWrapper(z.open(ref['transaction']), encoding='utf-8'))
        registers_df = pd.read_csv(io.TextIOWrapper(z.open(ref['register']), encoding='utf-8'))
        
    if 'reg_id' in registers_df.columns: # v3
        # Convert to datetime objects
        registers_df['check_in'] = pd.to_datetime(registers_df['check_in'])
        registers_df['check_out'] = pd.to_datetime(registers_df['check_out'])
        transactions_df['transaction_time'] = pd.to_datetime(transactions_df['transaction_time'])
        transactions_df['modified_time'] = pd.to_datetime(transactions_df['modified_time'])

        # Pre-index for fast lookup
        customer_map = customer_df.set_index('id').to_dict('index')
        transaction_map = transactions_df.groupby('register_id')

        # Preload existing DB records (avoid repeated queries)
        existing_register_ids = {r.id for r in Register.query.all()}
        existing_customer_ids = {c.id_detail for c in Customer.query.all()}
        existing_transaction_ids = {t.id for t in Transaction.query.all()}

        for _, record in registers_df.iterrows():
            reg_id = record['id']

            if reg_id in existing_register_ids:
                print(f"Record {reg_id} exists.")
                continue

            # 🔹 Collect customer IDs dynamically
            customer_ids = [
                v for k, v in record.items()
                if k.startswith('customer_id') and not pd.isna(v)
            ]

            for cid in customer_ids:
                cust = customer_map.get(cid)
                if not cust:
                    continue

                if cust['id_detail'] not in existing_customer_ids:
                    db.session.add(Customer(**cust))
                    print(f"Added customer {cid}")

            # 🔹 Transactions
            if reg_id in transaction_map.groups:
                for _, txn in transaction_map.get_group(reg_id).iterrows():
                    txn_id = txn['id']

                    if txn_id not in existing_transaction_ids:
                        db.session.add(Transaction(**txn.to_dict()))
                        print(f"Added transaction {txn_id}")

            # 🔹 Add register
            db.session.add(Register(**record.to_dict()))
            print(f"Added register {reg_id}")

        db.session.commit()
        print("Import complete.")
    else: # < v3
        print('Received < v3')
        # Convert to datetime objects
        registers_df['cin'] = pd.to_datetime(registers_df['cin'])
        registers_df['cout'] = pd.to_datetime(registers_df['cout'])
        registers_df['cout'] = registers_df['cout'].fillna('')
        transactions_df['t'] = pd.to_datetime(transactions_df['t'])

        registers_df = registers_df.rename(columns={
            'id': 'reg_id', 
            'rno': 'room_id', 
            'cid': 'customer_id', 
            'rpd': 'rent_per_day',
            'pov': 'purpose_of_visit',
            'gb': 'gst_invoice',
            'cin': 'check_in', 
            'cout': 'check_out',
        })
        
        registers_df['ac'] = registers_df['ac'] == 'AC'
        registers_df['number_of_persons'] = 1

        transactions_df = transactions_df.rename(columns={
            'rid': 'register_id',
            'a': 'amount_paid',
            't': 'transaction_time',
            'm': 'payment_mode',
        })

        customer_df = customer_df.rename(columns={
            'n': 'name',
            'a': 'address',
            'p': 'phone',
            'it': 'id_type',
            'ip': 'id_detail',
        })

        customer_df['id_detail'] = customer_df['id_detail'].fillna('MISSING' + str(random.randint(1, 100000)))
        customer_df['id_type'] = customer_df['id_type'].fillna('AADHAR')
        customer_df['address'] = customer_df['address'].fillna('AADHAR')

        # Preload existing DB records (avoid repeated queries)
        existing_register_ids = {r.id for r in Register.query.all()}

        if len(existing_register_ids) > 0:
            return {'success': False, 'message': 'Unable to insert data. Some data already exists. Clear all data, then try again.'}
        
        rooms_df = rooms_df.rename(columns={
            'r': 'room_number', 
            'f': 'floor_number', 
            's': 'is_available', 
        })

        rooms_df['is_available'] = rooms_df['is_available'] == 2
        rooms_df['capacity'] = 1

        # Get the id we want to keep for each id_detail
        keeper_map = (
            customer_df
            .sort_values('id')  # optional: ensures smallest id is kept
            .drop_duplicates(subset='id_detail', keep='first')
            .set_index('id_detail')['id']
        )

        # Add a column showing which id should be used
        customer_df['keeper_id'] = customer_df['id_detail'].map(keeper_map)

        # Create mapping from old id → keeper id
        id_map = customer_df.set_index('id')['keeper_id']

        # Update register_df
        registers_df['customer_id'] = registers_df['customer_id'].map(id_map)

        # Keep only unique customers
        customer_df_clean = customer_df[customer_df['id'] == customer_df['keeper_id']].copy()

        # Drop helper column if not needed
        customer_df_clean = customer_df_clean.drop(columns=['keeper_id'])

        print('Data cleaned')

        try:
            # db.session.bulk_insert_mappings(Register, registers_df.to_dict(orient='records'))
            for idx, record in registers_df.iterrows():
                db.session.add(Register(**record.to_dict()))
            db.session.bulk_insert_mappings(Customer, customer_df_clean.to_dict(orient='records'))
            db.session.bulk_insert_mappings(Room, rooms_df.to_dict(orient='records'))
            db.session.bulk_insert_mappings(Transaction, transactions_df.to_dict(orient='records'))
            db.session.commit()
        except IntegrityError as err:
            print(err)
            print({'success': False, 'message': str(err)})
            db.session.rollback()
            db.session.commit()
        except Exception as err:
            print(err, 121)

        print({'success': True, 'message': 'Successfully imported.'})

        return {'success': True, 'message': 'Successfully imported.'}