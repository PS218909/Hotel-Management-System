from flask import Flask, render_template, request, redirect, flash, url_for
import json

from app.services.room import get_all_rooms
from app.routes.auth import auth_bp
from app.routes.customer import customer_bp
from app.routes.room import room_bp
from app.routes.register import register_bp
from app.routes.api import api_bp
from app.routes.report import report_bp
from app.routes.transaction import transaction_bp
from app.routes.migrate import migrate_bp
from app.extensions import db

def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    with app.app_context():
        db.init_app(app)
        db.create_all()
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(register_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(migrate_bp)

    @app.route('/')
    def home():
        return redirect(url_for('room.list_rooms'))
    
    @app.route('/config/new', methods=['POST'])
    def _add_new_config():
        json_data = json.load(open('instance\\config.json', 'r'))
        json_data[request.form.get('key')] = request.form.get('value')
        json.dump(json_data, open('instance\\config.json', 'w'), indent=4)
        return redirect(request.referrer)

    @app.route('/admin', methods=['GET', 'POST'])
    def admin_dashboard():
        if request.method == 'POST':
            json.dump(request.form, open('instance\\config.json', 'w'), indent=4)
            flash('Upadted Successfully.')
            return redirect(url_for('admin_dashboard'))
        all_rooms = get_all_rooms()
        unique_floors = list(set([i.floor_number for i in all_rooms]))
        return render_template('admin/index.html', rooms=all_rooms, unique_floors=unique_floors, json_data=json.load(open('instance\\config.json', 'r')))
    
    return app