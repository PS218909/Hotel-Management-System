from app.models.user import User
from app.models.room import Room
from app.models.register import Register
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.extensions import db
from sqlalchemy import case, func, or_

from datetime import datetime, timedelta

def get_register_by_id(register_id):
    register = Register.query.get(int(register_id))
    return register

def create_register(**kwargs):
    try:
        register = Register(**kwargs)
        db.session.add(register)
        db.session.commit()
        return register
    except Exception as e:
        db.session.rollback()
        print(f'Error creating register: {e}')
        return None

def alter_register(register_id, **kwargs):
    register = get_register_by_id(register_id)
    if not register:
        return None
    for key, value in kwargs.items():
        if hasattr(register, key):
            setattr(register, key, value)
    db.session.commit()
    return register

def delete_register(register_id):
    register = get_register_by_id(register_id)
    if not register:
        return False
    db.session.delete(register)
    db.session.commit()
    return True

def delete_all_record():
    db.session.query(Register).delete(synchronize_session='fetch')
    rooms = Room.query.all()
    for room in rooms:
        room.is_available = True
    db.session.query(Customer).delete(synchronize_session='fetch')
    db.session.query(Transaction).delete(synchronize_session='fetch')
    db.session.commit()
    return

def get_all_registers(page = 1, per_page=10):
    return Register.query.order_by(
        case(
            (Register.check_out == None, 0), else_=1
        ), Register.check_in.desc()
    ).paginate(page=page, per_page=per_page)

def get_registers_by_customer(customer_id):
    return Register.query.filter(
        or_(Register.customer_id==customer_id, 
        Register.customer_id_2==customer_id,
        Register.customer_id_3==customer_id,
        Register.customer_id_4==customer_id,
        Register.customer_id_5==customer_id,
        Register.customer_id_6==customer_id,
        Register.customer_id_7==customer_id,
        Register.customer_id_8==customer_id,
        Register.customer_id_9==customer_id,
        Register.customer_id_10==customer_id,
        Register.customer_id_11==customer_id,
        Register.customer_id_12==customer_id)
    ).all()

def get_registers_by_room(room_id):
    return Register.query.filter_by(room_id=room_id).all()

def get_active_registers():
    return Register.query.filter(Register.check_out == None).all()

def get_past_registers():
    from datetime import date
    today = date.today()
    return Register.query.filter(Register.check_out < today).all()

def get_register_by_current_stay(room_id):
    return Register.query.filter(Register.room_id == room_id, (Register.check_out == None)).first()

def get_register_by_date(year, month, day):
    return Register.query.filter(func.extract('month', Register.check_in) == month, func.extract('year', Register.check_in) == year, func.extract('day', Register.check_in) == day).all()

def get_register_group_by_date(year, month):
    res = []
    for day in range(1, 32):
        try:
            datetime(year=int(year), month=int(month), day=int(day)) # Date Check
            res.append({'date': f'{day:02d}-{month}-{year}', 'count': len(get_register_by_date(year, month, day))})
        except Exception as err:
            print(err)
            break
    return res
    

def search_registers(**kwargs):
    query = Register.query.join(Register.customer).join(Register.room) # pyright: ignore[reportArgumentType]

    filter_map = {
        'name': lambda v: Customer.name.ilike(f"{v}%"),
        'address': lambda v: Customer.address.ilike(f"%{v}%"),
        'phone': lambda v: Customer.phone.like(f"%{v}%"),
        'room_no': lambda v: Room.room_number == v,
    }

    for key, value in kwargs.items():
        if not value:
            continue

        if key in filter_map:
            query = query.filter(filter_map[key](value))

    if kwargs.get('check_in'):
        day = datetime.strptime(kwargs['check_in'], "%Y-%m-%d")
        next_day = day + timedelta(days=1)

        query = query.filter(
            Register.check_in >= day,
            Register.check_in < next_day
        )
    if kwargs.get('check_out'):
        day = datetime.strptime(kwargs['check_out'], "%Y-%m-%d")
        next_day = day + timedelta(days=1)

        query = query.filter(
            Register.check_out >= day,
            Register.check_out < next_day
        )
    
    check_out_expr = func.coalesce(Register.check_out, func.current_timestamp())
    diff_seconds_expr = func.strftime('%s', check_out_expr) - func.strftime('%s', Register.check_in)  # SQLite seconds
    full_days_expr = func.floor(diff_seconds_expr / 86400)  # 86400 seconds = 1 day
    days_expr = case(
        (diff_seconds_expr % 86400 < 2 * 3600, full_days_expr - 1),
        else_=full_days_expr
    )
    days_expr = case(
        (days_expr < 1, 1),
        else_=days_expr
    )

    # Total rent
    total_rent_expr = days_expr * Register.rent_per_day

    # Remaining balance = total_rent - total_paid
    remaining_balance_expr = total_rent_expr - func.coalesce(Register.total_paid, 0)

    if kwargs.get('remain_balance_gt'):
        query = query.filter(remaining_balance_expr > int(kwargs.get('remain_balance_gt', '0')))
    
    if kwargs.get('remain_balance_lt'):
        query = query.filter(remaining_balance_expr < int(kwargs.get('remain_balance_lt', '0')))
    
    query = query.order_by(
        case(
            (Register.check_out == None, 0), else_=1
        ), (Register.check_in.desc())
    )
    return query.paginate(page=int(kwargs['page']), per_page=int(kwargs['per_page']), error_out=False)