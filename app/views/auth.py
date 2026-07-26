from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app import db
from app.models import User
from app.forms import RegistrationForm, LoginForm
from app.email_service import send_confirmation_email, confirm_token, generate_confirmation_token

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        email_sent = send_confirmation_email(user)
        if email_sent:
            flash('На ваш email отправлено письмо для подтверждения регистрации.')
        else:
            confirm_url = url_for('auth.confirm_email', token=generate_confirmation_token(user.email), _external=True)
            flash(f'Не удалось отправить письмо. Если вы ввели реальный email, попробуйте позже. '
                  f'Для тестирования перейдите по ссылке: {confirm_url}')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash('Ссылка недействительна или истек срок её действия.')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first_or_404()
    if user.email_confirmed:
        flash('Email уже подтверждён. Вы можете войти.')
    else:
        user.email_confirmed = True
        db.session.commit()
        flash('Email успешно подтверждён! Теперь вы можете войти.')
    return redirect(url_for('auth.login'))


@auth_bp.route('/resend-confirmation/<email>')
def resend_confirmation(email):
    user = User.query.filter_by(email=email).first_or_404()
    if user.email_confirmed:
        flash('Email уже подтверждён.')
    else:
        if send_confirmation_email(user):
            flash('Письмо повторно отправлено.')
        else:
            flash('Не удалось отправить письмо. Попробуйте позже.')
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверный email или пароль.')
            return redirect(url_for('auth.login'))

        if not user.email_confirmed:
            flash('Пожалуйста, сначала подтвердите ваш email.')
            return render_template('auth/login.html', form=form, unconfirmed_email=user.email)

        login_user(user)

        role_redirects = {
            'admin': 'admin.dashboard',
            'teacher': 'dashboard.teacher',
            'student': 'dashboard.student',
        }
        return redirect(url_for(role_redirects.get(user.role, 'dashboard.student')))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
