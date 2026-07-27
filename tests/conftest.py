import os
import threading
import time
import pytest

_TEST_DB_PATH = os.path.join(os.path.dirname(__file__), 'test_app.db')
os.environ['DATABASE_URL'] = f'sqlite:///{_TEST_DB_PATH}'

from werkzeug.serving import make_server
from app import create_app, db
from app.models import User


def seed_database():
    admin = User(
        email='admin@lang.ru', username='admin',
        first_name='Admin', last_name='Adminov',
        role='admin', email_confirmed=True,
    )
    admin.set_password('admin123')

    teachers = [
        User(
            email=f'teacher{i}@lang.ru', username=f'teacher{i}',
            first_name='Teacher', last_name=f'#{i}',
            role='teacher', email_confirmed=True,
        )
        for i in range(1, 3)
    ]
    for t in teachers:
        t.set_password('teacher123')

    students = [
        User(
            email=f'student{i}@lang.ru', username=f'student{i}',
            first_name='Student', last_name=f'#{i}',
            role='student', email_confirmed=True,
        )
        for i in range(1, 11)
    ]
    for s in students:
        s.set_password('student123')

    db.session.add(admin)
    db.session.add_all(teachers)
    db.session.add_all(students)
    db.session.commit()
    return admin, teachers, students


@pytest.fixture(scope='session')
def app():
    if os.path.exists(_TEST_DB_PATH):
        os.remove(_TEST_DB_PATH)
    app = create_app()
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'MAIL_SUPPRESS_SEND': True,
    })
    return app


@pytest.fixture(scope='session', autouse=True)
def setup_db(app):
    with app.app_context():
        db.create_all()
        seed_database()
        yield
        db.drop_all()
        if os.path.exists(_TEST_DB_PATH):
            try:
                os.remove(_TEST_DB_PATH)
            except PermissionError:
                pass


@pytest.fixture(scope='session')
def live_server(app):
    server = make_server('127.0.0.1', 0, app)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    time.sleep(0.3)
    yield f'http://127.0.0.1:{port}'
    server.shutdown()
