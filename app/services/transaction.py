from app.models.transaction import Transaction
from app.models.register import Register
from app.models.customer import Customer
from app.models.room import Room
from app.extensions import db

from datetime import datetime, timedelta

def create_transaction(**kwargs):
    new_transaction = Transaction(**kwargs)
    db.session.add(new_transaction)
    db.session.commit()
    return new_transaction

def get_transaction_by_id(transaction_id):
    return Transaction.query.get(transaction_id)

def get_transaction_by_register_id(register_id):
    return Transaction.query.filter_by(register_id=register_id)

def get_all_transactions():
    return (
        db.session.query(
            Transaction.transaction_time,
            Room.room_number,
            Customer.name,
            Transaction.amount_paid,
            Transaction.payment_method,
            Transaction.id,
        )
        .outerjoin(Register, Transaction.register_id == Register.id)
        .outerjoin(Customer, Register.customer_id == Customer.id)
        .outerjoin(Room, Register.room_id == Room.id)
        .order_by(Transaction.transaction_time.asc())
        .all()
    )

def get_all_transaction_api(**kwargs):
    query = db.session.query(
        Transaction.transaction_time,
        Room.room_number,
        Customer.name,
        Transaction.amount_paid,
        Transaction.payment_method,
        Transaction.id,
    ).outerjoin(
        Register, Transaction.register_id == Register.id
    ).outerjoin(
        Customer, Register.customer_id == Customer.id
    ).outerjoin(
        Room, Register.room_id == Room.id
    )
    if kwargs.get('name'):
        query = query.filter(Customer.name.ilike(f'{kwargs['name']}%'))
    if kwargs.get('payment_method'):
        query = query.filter(Transaction.payment_method.ilike(f'{kwargs['payment_method']}%'))
    if kwargs.get('transaction_date'):
        day = datetime.strptime(kwargs['transaction_date'], "%Y-%m-%d")
        next_day = day + timedelta(days=1)
        query = query.filter(Transaction.transaction_time >= day , Transaction.transaction_time < next_day)
    query = query.order_by(Transaction.transaction_time.desc(), Transaction.id)
    page = int(kwargs.get('page', 0)) - 1
    per_page = int(kwargs.get('per_page', 10))
    offset = (page) * per_page
    query = query.limit(per_page).offset(offset)
    return query.all()

def get_transactions_by_customer_id(id):
    return (
        db.session.query(
            Transaction.transaction_time,
            Room.room_number,
            Customer.name,
            Transaction.amount_paid,
            Transaction.payment_method,
            Transaction.id,
        )
        .outerjoin(Register, Transaction.register_id == Register.id)
        .outerjoin(Customer, Register.customer_id == Customer.id)
        .outerjoin(Customer, id == Customer.id)
        .outerjoin(Room, Register.room_id == Room.id)
        .order_by(Transaction.transaction_time.asc())
        .all()
    )

def delete_transaction(transaction_id):
    transaction = Transaction.query.get(transaction_id)
    if transaction:
        db.session.delete(transaction)
        db.session.commit()
        return True
    return False

def update_transaction(transaction_id, amount_paid=None, payment_method=None):
    transaction = Transaction.query.get(transaction_id)
    if transaction:
        if amount_paid is not None:
            transaction.amount_paid = amount_paid
        if payment_method is not None:
            transaction.payment_method = payment_method
        transaction.update_timestamp()
        db.session.commit()
        return transaction
    return None

