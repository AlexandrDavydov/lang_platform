from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import role_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/student')
@login_required
@role_required('student')
def student():
    return render_template('student/dashboard.html')


@dashboard_bp.route('/teacher')
@login_required
@role_required('teacher')
def teacher():
    return render_template('teacher/dashboard.html')
