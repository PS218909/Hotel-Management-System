from app.extensions import db

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    register_id = db.Column(db.Integer, db.ForeignKey('register.id'))
    amount_paid = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String, nullable=False)
    transaction_time = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    modified_time = db.Column(db.DateTime, nullable=True, default=db.func.current_timestamp())

    register = db.relationship('Register', backref='Transaction')

    def __repr__(self):
        return f'Transaction by {self.register.customer.name} on {self.transaction_time} - ₹ {self.amount_paid} via {self.payment_method}'
    
    def update_timestamp(self):
        self.modified_time = db.func.current_timestamp()