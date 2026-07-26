import calendar
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, ScheduleLesson
from app.forms import ScheduleLessonForm
from app.decorators import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    users = User.query.all()
    return render_template('admin/dashboard.html', users=users)


@admin_bp.route('/set_role/<int:user_id>/<role>')
@login_required
@role_required('admin')
def set_role(user_id, role):
    if role not in ('student', 'teacher'):
        flash('Недопустимая роль.')
        return redirect(url_for('admin.dashboard'))

    user = db.session.get(User, user_id)
    if not user:
        flash('Пользователь не найден.')
        return redirect(url_for('admin.dashboard'))

    user.role = role
    db.session.commit()
    flash(f'Роль пользователя {user.username} изменена на "{role}".')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/confirm_user/<int:user_id>')
@login_required
@role_required('admin')
def confirm_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('Пользователь не найден.')
    elif user.email_confirmed:
        flash('Email уже подтверждён.')
    else:
        user.email_confirmed = True
        db.session.commit()
        flash(f'Email пользователя {user.username} подтверждён.')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/schedule')
@admin_bp.route('/schedule/<int:year>/<int:month>')
@login_required
@role_required('admin')
def schedule(year=None, month=None):
    today = date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)

    cal_prev = (month - 1) if month > 1 else 12
    cal_prev_year = year if month > 1 else year - 1
    cal_next = (month + 1) if month < 12 else 1
    cal_next_year = year if month < 12 else year + 1

    month_name = calendar.month_name[month]

    lessons = ScheduleLesson.query.filter(
        db.extract('year', ScheduleLesson.date) == year,
        db.extract('month', ScheduleLesson.date) == month,
    ).all()

    lesson_dates = {str(l.date) for l in lessons}

    return render_template(
        'admin/schedule.html',
        year=year, month=month, month_name=month_name,
        month_days=month_days,
        cal_prev=cal_prev, cal_prev_year=cal_prev_year,
        cal_next=cal_next, cal_next_year=cal_next_year,
        today=today, lesson_dates=lesson_dates,
    )


@admin_bp.route('/schedule/<string:lesson_date>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def schedule_day(lesson_date):
    try:
        dt = date.fromisoformat(lesson_date)
    except ValueError:
        flash('Неверная дата.')
        return redirect(url_for('admin.schedule'))

    students = User.query.filter_by(role='student').all()
    form = ScheduleLessonForm()
    form.student.choices = [(s.id, f'{s.first_name} {s.last_name}') for s in students]
    form.date.data = dt

    if form.validate_on_submit():
        lesson = ScheduleLesson(
            student_id=form.student.data,
            title=form.title.data,
            date=form.date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
        )
        db.session.add(lesson)
        db.session.commit()
        flash('Занятие добавлено.')
        return redirect(url_for('admin.schedule_day', lesson_date=lesson_date))

    lessons = ScheduleLesson.query.filter_by(date=dt).order_by(ScheduleLesson.start_time).all()
    return render_template('admin/schedule_day.html', date=dt, lessons=lessons, form=form, students=students)


@admin_bp.route('/schedule/<string:lesson_date>/edit/<int:lesson_id>', methods=['POST'])
@login_required
@role_required('admin')
def edit_lesson(lesson_date, lesson_id):
    lesson = db.session.get(ScheduleLesson, lesson_id)
    if not lesson:
        flash('Занятие не найдено.')
        return redirect(url_for('admin.schedule_day', lesson_date=lesson_date))

    students = User.query.filter_by(role='student').all()
    form = ScheduleLessonForm()
    form.student.choices = [(s.id, f'{s.first_name} {s.last_name}') for s in students]

    if form.validate_on_submit():
        lesson.student_id = form.student.data
        lesson.title = form.title.data
        lesson.date = form.date.data
        lesson.start_time = form.start_time.data
        lesson.end_time = form.end_time.data
        db.session.commit()
        flash('Занятие обновлено.')
        return redirect(url_for('admin.schedule_day', lesson_date=lesson.date.isoformat()))

    return redirect(url_for('admin.schedule_day', lesson_date=lesson_date))


@admin_bp.route('/schedule/api/lesson/<int:lesson_id>')
@login_required
@role_required('admin')
def api_lesson(lesson_id):
    lesson = db.session.get(ScheduleLesson, lesson_id)
    if not lesson:
        return jsonify({'error': 'not found'}), 404
    return jsonify({
        'student_id': lesson.student_id,
        'title': lesson.title,
        'date': lesson.date.isoformat(),
        'start_time': lesson.start_time.strftime('%H:%M'),
        'end_time': lesson.end_time.strftime('%H:%M'),
    })


@admin_bp.route('/schedule/<string:lesson_date>/delete/<int:lesson_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_lesson(lesson_date, lesson_id):
    lesson = db.session.get(ScheduleLesson, lesson_id)
    if lesson:
        db.session.delete(lesson)
        db.session.commit()
        flash('Занятие удалено.')
    return redirect(url_for('admin.schedule_day', lesson_date=lesson_date))
