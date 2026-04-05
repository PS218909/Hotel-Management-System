from app.extensions import db
from sqlalchemy import func, select
from sqlalchemy.orm import column_property
from app.models.transaction import Transaction

class Register(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_id = db.Column(db.Integer, unique=False, nullable=True)
    number_of_persons = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=True)
    rent_per_day = db.Column(db.Float, nullable=False)
    gst_invoice = db.Column(db.Integer, nullable=True)
    gst_number = db.Column(db.String, nullable=True)
    gst_total_amount = db.Column(db.Integer, nullable=True)
    purpose_of_visit = db.Column(db.String, nullable=False)
    ac = db.Column(db.Boolean, default=False)
    customer_id_2 = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_id_3 = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_id_4 = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_id_5 = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_id_6 = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_id_7 = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_id_8 = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_id_9 = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_id_10 = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_id_11 = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_id_12 = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    notes = db.Column(db.String, nullable=True)
    room = db.relationship('Room', backref='register')
    customer = db.relationship('Customer', foreign_keys=[customer_id], backref='register')

    total_paid = column_property(
        select(
            func.coalesce(func.sum(Transaction.amount_paid), 0)
        )
        .where(Transaction.register_id == id)
        .correlate_except(Transaction)
        .scalar_subquery()
    )

    def __repr__(self):
        return f'Register {self.id} - Customer ID: {self.customer_id}, Room ID: {self.room_id}'
    
    def get_customer_list(self):
        return {
            'customer_id': {'id': self.customer_id},
            'customer_id_2': {'id': self.customer_id_2},
            'customer_id_3': {'id': self.customer_id_3},
            'customer_id_4': {'id': self.customer_id_4},
            'customer_id_5': {'id': self.customer_id_5},
            'customer_id_6': {'id': self.customer_id_6},
            'customer_id_7': {'id': self.customer_id_7},
            'customer_id_8': {'id': self.customer_id_8},
            'customer_id_9': {'id': self.customer_id_9},
            'customer_id_10': {'id': self.customer_id_10},
            'customer_id_11': {'id': self.customer_id_11},
            'customer_id_12': {'id': self.customer_id_12},
        }