from flask import Blueprint, request, jsonify, render_template, send_file, flash, redirect
from datetime import datetime
import os

from app.services.register import get_register_group_by_date, get_register_by_date
from app.util.helper import generate_docx_report, register_records_to_array, get_config

report_bp = Blueprint('report', __name__, url_prefix='/report')

@report_bp.route('/')
def report():
    period = request.args.get('period', default=None)
    if not period:
        period = datetime.now().strftime('%Y-%m')
    year, month = period.split('-')
    result = get_register_group_by_date(year, month)
    return render_template('analysis/report.html', period=period, records=result)

@report_bp.route('/<date>')
def send_report(date):
    if date.count('-') == 2:
        day, month, year = date.split('-')
    else:
        flash('Invalid Date Passed', category='error')
        return redirect('report')
    config = get_config()
    report_path = config.get('REPORT_PATH', None)
    file_stream = generate_docx_report(get_register_by_date(year, month, day), date)
    if not report_path:
        return send_file(file_stream, download_name=date + '.docx', as_attachment=True)
    else:
        monthly_report_folder = config.get('MONTHLY_REPORT_FOLDER', 'False')
        os.makedirs(report_path, exist_ok=True)
        file_name = report_path
        if monthly_report_folder == 'True':
            file_name = os.path.join(report_path, datetime(year=int(year), month=int(month), day=int(day)).strftime('%B'))
            os.makedirs(file_name, exist_ok=True)
        os.startfile(file_name)
        file_name = os.path.join(file_name, date+'.docx')
        with open(file_name, 'wb') as f:
            f.write(file_stream.getvalue())
        return redirect(request.referrer)