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

def import_data(zip_file):
    ref = {}
    with zipfile.ZipFile(zip_file, 'r') as zip:
        for name in zip.namelist():
            if name.endswith('.csv'):
                if 'customer' in name:
                    ref['customer'] = name
                if 'room' in name:
                    ref['room'] = name
                if 'transaction' in name:
                    ref['transaction'] = name
                if 'register' in name:
                    ref['register'] = name
        customer = io.TextIOWrapper(zip.open(ref['customer']), encoding='utf-8')
        rooms = io.TextIOWrapper(zip.open(ref['room']), encoding='utf-8')
        transactions = io.TextIOWrapper(zip.open(ref['transaction']), encoding='utf-8')
        registers = io.TextIOWrapper(zip.open(ref['register']), encoding='utf-8')

        customer_df = pd.read_csv(customer)
        rooms_df = pd.read_csv(rooms)
        transactions_df = pd.read_csv(transactions)
        registers_df = pd.read_csv(registers)

        customer.close()
        rooms.close()
        transactions.close()
        registers.close()

        if 'reg_id' in registers_df.columns:
            for idx, record in registers_df.iterrows():
                record_exist = Register.query.filter(Register.id == record['id'])
                if not record_exist:
                    customer_ids = [record['customer_id']]
                    for i in range(2, 13):
                        if not pd.isna(record['customer_id_' + str(i)]):
                            customer_ids.append(record['customer_id_' + str(i)])
                    for customer_id in customer_ids:
                        customer = customer_df[customer_df['id'] == customer_id]
                        customer_exist = Customer.query.filter(Customer.id_detail == customer['id_detail'])
                        if not customer_exist:
                            # db.session.add(Customer(**customer.to_dict('record')))
                            print(customer)
                    
                    transaction_ids = transactions_df[transactions_df['register_id'] == record['id']]
                    for transaction_id in transaction_ids:
                        print(transaction_id)

                    # db.session.add(Register(**record.to_dict('record')))
                    # db.session.commit()
                    print(record.to_dict())
        else:
            for idx, record in registers_df.iterrows():
                record_exist = Register.query.filter(Register.id == record['id'])
                if not record_exist:
                    pass