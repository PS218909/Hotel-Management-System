from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User

def authenticate(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user
    return None

def get_user_by_id(user_id):
    return User.query.get(int(user_id))

def create_user(username, password, role):
    try:
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None
    return user

def alter_user(user_id, **kwargs):
    user = get_user_by_id(user_id)
    if not user:
        return None
    for key, value in kwargs.items():
        if key == 'password':
            user.set_password(value)
        elif hasattr(user, key):
            setattr(user, key, value)
    db.session.commit()
    return user