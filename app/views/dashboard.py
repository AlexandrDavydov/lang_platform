import calendar
from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.decorators import role_required
from app.models import User, ScheduleLesson, Lesson
from app.forms import TeacherLessonForm

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

    assigned_lessons = Lesson.query.filter(Lesson.students.any(id=current_user.id)).order_by(Lesson.created_at.desc()).all()

    return render_template('student/dashboard.html', upcoming=upcoming, past=past, assigned_lessons=assigned_lessons)


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


@dashboard_bp.route('/teacher/schedule')
@dashboard_bp.route('/teacher/schedule/<int:year>/<int:month>')
@login_required
@role_required('teacher')
def teacher_schedule(year=None, month=None):
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
        ScheduleLesson.teacher_id == current_user.id,
        db.extract('year', ScheduleLesson.date) == year,
        db.extract('month', ScheduleLesson.date) == month,
    ).all()

    lesson_dates = {str(l.date) for l in lessons}

    return render_template(
        'teacher/schedule.html',
        year=year, month=month, month_name=month_name,
        month_days=month_days,
        cal_prev=cal_prev, cal_prev_year=cal_prev_year,
        cal_next=cal_next, cal_next_year=cal_next_year,
        today=today, lesson_dates=lesson_dates,
    )


@dashboard_bp.route('/teacher/schedule/<string:lesson_date>', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def teacher_schedule_day(lesson_date):
    try:
        dt = date.fromisoformat(lesson_date)
    except ValueError:
        flash('Неверная дата.')
        return redirect(url_for('dashboard.teacher_schedule'))

    students = User.query.filter_by(role='student').all()
    form = TeacherLessonForm()
    form.student.choices = [(s.id, f'{s.first_name} {s.last_name}') for s in students]
    form.date.data = dt

    if form.validate_on_submit():
        if ScheduleLesson.has_conflict(current_user.id, form.date.data, form.start_time.data, form.end_time.data):
            flash('Вы уже заняты в это время.')
        elif ScheduleLesson.has_conflict(form.student.data, form.date.data, form.start_time.data, form.end_time.data):
            flash('Ученик уже занят в это время.')
        else:
            lesson = ScheduleLesson(
                student_id=form.student.data,
                teacher_id=current_user.id,
                title=form.title.data,
                date=form.date.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
            )
            db.session.add(lesson)
            db.session.commit()
            flash('Занятие добавлено.')
        return redirect(url_for('dashboard.teacher_schedule_day', lesson_date=lesson_date))

    lessons = ScheduleLesson.query.filter_by(
        date=dt, teacher_id=current_user.id
    ).order_by(ScheduleLesson.start_time).all()
    return render_template(
        'teacher/schedule_day.html', date=dt, lessons=lessons, form=form, students=students
    )


@dashboard_bp.route('/teacher/schedule/<string:lesson_date>/edit/<int:lesson_id>', methods=['POST'])
@login_required
@role_required('teacher')
def teacher_edit_lesson(lesson_date, lesson_id):
    lesson = db.session.get(ScheduleLesson, lesson_id)
    if not lesson or lesson.teacher_id != current_user.id:
        flash('Занятие не найдено.')
        return redirect(url_for('dashboard.teacher_schedule_day', lesson_date=lesson_date))

    students = User.query.filter_by(role='student').all()
    form = TeacherLessonForm()
    form.student.choices = [(s.id, f'{s.first_name} {s.last_name}') for s in students]

    if form.validate_on_submit():
        if ScheduleLesson.has_conflict(current_user.id, form.date.data, form.start_time.data, form.end_time.data, exclude_id=lesson.id):
            flash('Вы уже заняты в это время.')
        elif ScheduleLesson.has_conflict(form.student.data, form.date.data, form.start_time.data, form.end_time.data, exclude_id=lesson.id):
            flash('Ученик уже занят в это время.')
        else:
            lesson.student_id = form.student.data
            lesson.title = form.title.data
            lesson.date = form.date.data
            lesson.start_time = form.start_time.data
            lesson.end_time = form.end_time.data
            db.session.commit()
            flash('Занятие обновлено.')
        return redirect(url_for('dashboard.teacher_schedule_day', lesson_date=lesson.date.isoformat()))

    return redirect(url_for('dashboard.teacher_schedule_day', lesson_date=lesson_date))


@dashboard_bp.route('/teacher/schedule/api/lesson/<int:lesson_id>')
@login_required
@role_required('teacher')
def teacher_api_lesson(lesson_id):
    lesson = db.session.get(ScheduleLesson, lesson_id)
    if not lesson or lesson.teacher_id != current_user.id:
        return jsonify({'error': 'not found'}), 404
    return jsonify({
        'student_id': lesson.student_id,
        'title': lesson.title,
        'date': lesson.date.isoformat(),
        'start_time': lesson.start_time.strftime('%H:%M'),
        'end_time': lesson.end_time.strftime('%H:%M'),
    })


@dashboard_bp.route('/teacher/schedule/<string:lesson_date>/delete/<int:lesson_id>', methods=['POST'])
@login_required
@role_required('teacher')
def teacher_delete_lesson(lesson_date, lesson_id):
    lesson = db.session.get(ScheduleLesson, lesson_id)
    if lesson and lesson.teacher_id == current_user.id:
        db.session.delete(lesson)
        db.session.commit()
        flash('Занятие удалено.')
    return redirect(url_for('dashboard.teacher_schedule_day', lesson_date=lesson_date))
