from app.extensions import db

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String, nullable=False, unique=True)
    floor_number = db.Column(db.String, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    is_available = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'Room {self.room_number} is - {"available" if self.is_available else "occupied"}'