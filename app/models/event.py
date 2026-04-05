from app.extensions import db
from sqlalchemy import func

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    operation = db.Column(db.String, nullable=False)
    detail = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f'Event {self.id} - User ID: {self.user_id}, Operation: {self.operation}'