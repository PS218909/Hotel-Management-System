from sqlalchemy.exc import IntegrityError

from app.models.room import Room
from app.models.register import Register
from app.extensions import db

def get_room_by_id(room_id):
    return Room.query.get(int(room_id))

def create_room(room_number, floor_number, capacity = 2, is_available=True):
    try:
        room = Room(room_number=room_number, floor_number=floor_number, capacity=capacity, is_available=is_available) # type: ignore
        db.session.add(room)
        db.session.commit()
        return room
    except IntegrityError as err:
        print(err)
        db.session.rollback()
        return None

def alter_room(room_id, **kwargs):
    room = get_room_by_id(room_id)
    if not room:
        return None
    for key, value in kwargs.items():
        if hasattr(room, key):
            setattr(room, key, value)
    db.session.commit()
    return room

def delete_room(room_id):
    room = get_room_by_id(room_id)
    if Register.query.filter(Register.room_id == room_id).all():
        return False
    if not room:
        return False
    db.session.delete(room)
    db.session.commit()
    return True

def get_all_rooms():
    return Room.query.all()

def get_available_rooms():
    return Room.query.filter_by(is_available=True).all()

def get_unavailable_rooms():
    return Room.query.filter_by(is_available=False).all()

def get_rooms_by_floor(floor_number):
    return Room.query.filter_by(floor_number=floor_number).all()

def find_room(**kwargs):
    query = Room.query
    for key, value in kwargs.items():
        if hasattr(Room, key):
            query = query.filter(getattr(Room, key) == value)
    return query.all()