from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, SelectMultipleField, DateField, TimeField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional
from app.models import User


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Имя пользователя', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Этот email уже зарегистрирован.')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Это имя пользователя уже занято.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class ScheduleLessonForm(FlaskForm):
    student = SelectField('Ученик', coerce=int, validators=[DataRequired()])
    teacher = SelectField('Учитель', coerce=int, validators=[DataRequired()])
    title = StringField('Название занятия', validators=[DataRequired()])
    date = DateField('Дата', format='%Y-%m-%d', validators=[DataRequired()])
    start_time = TimeField('Начало', format='%H:%M', validators=[DataRequired()])
    end_time = TimeField('Конец', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Сохранить')


class TeacherLessonForm(FlaskForm):
    student = SelectField('Ученик', coerce=int, validators=[DataRequired()])
    title = StringField('Название занятия', validators=[DataRequired()])
    date = DateField('Дата', format='%Y-%m-%d', validators=[DataRequired()])
    start_time = TimeField('Начало', format='%H:%M', validators=[DataRequired()])
    end_time = TimeField('Конец', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Сохранить')


class LessonForm(FlaskForm):
    title = StringField('Название урока', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[Optional()])
    students = SelectMultipleField('Ученики', coerce=int, validators=[Optional()])
    materials = SelectMultipleField('Материалы', coerce=int, validators=[Optional()])
    submit = SubmitField('Сохранить')


class MaterialForm(FlaskForm):
    title = StringField('Название материала', validators=[DataRequired()])
    content = TextAreaField('Содержание', validators=[Optional()])
    material_type = SelectField('Тип', choices=[
        ('text', 'Текст'),
        ('link', 'Ссылка'),
        ('image', 'Изображение'),
    ])
    file_url = StringField('URL / Ссылка', validators=[Optional()])
    submit = SubmitField('Сохранить')
