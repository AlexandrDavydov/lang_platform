from flask import current_app, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from app import mail


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm')


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token, salt='email-confirm', max_age=expiration)
    except Exception:
        return None
    return email


def send_confirmation_email(user):
    token = generate_confirmation_token(user.email)
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    subject = 'Подтверждение регистрации'
    html = f'''
    <h1>Добро пожаловать, {user.username}!</h1>
    <p>Для завершения регистрации перейдите по ссылке:</p>
    <p><a href="{confirm_url}">{confirm_url}</a></p>
    <p>Ссылка действительна в течение 1 часа.</p>
    '''
    msg = Message(subject, recipients=[user.email], html=html)
    try:
        mail.send(msg)
        return True
    except Exception:
        return False
