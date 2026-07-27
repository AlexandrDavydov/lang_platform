from datetime import date
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.decorators import role_required
from app.models import ScheduleLesson

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/student')
@login_required
@role_required('student')
def student():
    today = date.today()
    upcoming = ScheduleLesson.query.filter(
        ScheduleLesson.student_id == current_user.id,
        ScheduleLesson.date >= today,
    ).order_by(ScheduleLesson.date, ScheduleLesson.start_time).all()

    past = ScheduleLesson.query.filter(
        ScheduleLesson.student_id == current_user.id,
        ScheduleLesson.date < today,
    ).order_by(ScheduleLesson.date.desc(), ScheduleLesson.start_time).all()

    return render_template('student/dashboard.html', upcoming=upcoming, past=past)


@dashboard_bp.route('/teacher')
@login_required
@role_required('teacher')
def teacher():
    today = date.today()
    upcoming = ScheduleLesson.query.filter(
        ScheduleLesson.teacher_id == current_user.id,
        ScheduleLesson.date >= today,
    ).order_by(ScheduleLesson.date, ScheduleLesson.start_time).all()

    past = ScheduleLesson.query.filter(
        ScheduleLesson.teacher_id == current_user.id,
        ScheduleLesson.date < today,
    ).order_by(ScheduleLesson.date.desc(), ScheduleLesson.start_time).all()

    return render_template('teacher/dashboard.html', upcoming=upcoming, past=past)
