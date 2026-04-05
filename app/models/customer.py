from sqlalchemy import func
from sqlalchemy.orm import object_session

from app.extensions import db
from app.models.register import Register

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String)
    address = db.Column(db.String, nullable=False)
    id_type = db.Column(db.String, nullable=False)
    id_detail = db.Column(db.String, nullable=False, unique=True)

    def __repr__(self):
        return 'Name: ' + self.name + '\tPhone: ' + str(self.phone) + '\tAddress: ' + self.address
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'id_type': self.id_type,
            'id_detail': self.id_detail,
        }