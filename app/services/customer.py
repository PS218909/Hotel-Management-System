from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.customer import Customer

def get_customer_by_id(customer_id):
    return Customer.query.get(int(customer_id))

def create_customer(**kwargs):
    try:
        customer = Customer(**kwargs)
        db.session.add(customer)
        db.session.commit()
        return customer
    except IntegrityError as err:
        print(err)
        db.session.rollback()
        return None

def alter_customer(customer_id, **kwargs):
    customer = get_customer_by_id(customer_id)
    if not customer:
        return None
    for key, value in kwargs.items():
        if hasattr(customer, key):
            setattr(customer, key, value)
    db.session.commit()
    return customer

def delete_customer(customer_id):
    customer = get_customer_by_id(customer_id)
    if not customer:
        return False
    db.session.delete(customer)
    db.session.commit()
    return True

def get_all_customers():
    return Customer.query.order_by(Customer.name).all()

def search_customers_by_multiple_fields(**kwargs):
    query = Customer.query
    for key, value in kwargs.items():
        if hasattr(Customer, key) and (value is not None) and value:
            query = query.filter(getattr(Customer, key).ilike(f"{value}%"))
    return query.all()