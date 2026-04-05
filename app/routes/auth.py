from flask import Blueprint, request, jsonify, redirect, url_for, session, render_template
from app.services.auth import authenticate, create_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if authenticate(username, password):
            session['user'] = username
            session.timeout = 3600 * 6
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401
    return render_template('auth.login.html')

@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.pop('user', None)
    return redirect(url_for('auth.login'))

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        create_user(username, password, role='staff')
        return jsonify({"message": "Signup successful"}), 201
    return render_template('auth.signup.html')