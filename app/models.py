from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


lesson_materials = db.Table('lesson_materials',
    db.Column('lesson_id', db.Integer, db.ForeignKey('lesson.id'), primary_key=True),
    db.Column('material_id', db.Integer, db.ForeignKey('material.id'), primary_key=True),
    db.Column('order', db.Integer, default=0),
)

lesson_students = db.Table('lesson_students',
    db.Column('lesson_id', db.Integer, db.ForeignKey('lesson.id'), primary_key=True),
    db.Column('student_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student')

    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))

    email_confirmed = db.Column(db.Boolean, default=False)
    registered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        return self.role == role

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class ScheduleLesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    student = db.relationship('User', backref='lessons', foreign_keys=[student_id])
    teacher = db.relationship('User', backref='taught_lessons', foreign_keys=[teacher_id])

    @staticmethod
    def has_conflict(user_id, date, start_time, end_time, exclude_id=None):
        query = ScheduleLesson.query.filter(
            ScheduleLesson.date == date,
            ScheduleLesson.start_time < end_time,
            ScheduleLesson.end_time > start_time,
            (ScheduleLesson.teacher_id == user_id) | (ScheduleLesson.student_id == user_id),
        )
        if exclude_id:
            query = query.filter(ScheduleLesson.id != exclude_id)
        return query.first() is not None

    def __repr__(self):
        return f'<Lesson {self.title} {self.date} {self.start_time}-{self.end_time}>'


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    created_by = db.relationship('User', backref='created_lessons', foreign_keys=[created_by_id])
    students = db.relationship('User', secondary=lesson_students, lazy='dynamic',
                               backref=db.backref('study_lessons', lazy='dynamic'))
    materials = db.relationship('Material', secondary=lesson_materials, lazy='dynamic',
                                order_by=lesson_materials.c.order,
                                backref=db.backref('lessons', lazy='dynamic'))

    def __repr__(self):
        return f'<Lesson {self.title}>'


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    material_type = db.Column(db.String(20), default='text')
    file_url = db.Column(db.String(500))
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    created_by = db.relationship('User', backref='created_materials')

    def __repr__(self):
        return f'<Material {self.title}>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
