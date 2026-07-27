from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()

    if User.query.first():
        print('База уже содержит пользователей. Очистите БД и запустите заново.')
        exit()

    admin = User(
        email='admin@lang.ru',
        username='admin',
        first_name='Админ',
        last_name='Админов',
        role='admin',
        email_confirmed=True,
    )
    admin.set_password('admin123')

    teachers = [
        User(
            email=f'teacher{i}@lang.ru',
            username=f'teacher{i}',
            first_name=f'Учитель',
            last_name=f'{i}-й',
            role='teacher',
            email_confirmed=True,
        )
        for i in range(1, 3)
    ]
    for t in teachers:
        t.set_password('teacher123')

    students = [
        User(
            email=f'student{i}@lang.ru',
            username=f'student{i}',
            first_name=f'Ученик',
            last_name=f'{i}-й',
            role='student',
            email_confirmed=True,
        )
        for i in range(1, 11)
    ]
    for s in students:
        s.set_password('student123')

    db.session.add(admin)
    db.session.add_all(teachers)
    db.session.add_all(students)

    db.session.commit()

    print()
    print('=' * 60)
    print('  Role     | Email                  | Password')
    print('=' * 60)
    print('  admin    | admin@lang.ru          | admin123')
    print('  teacher  | teacher1@lang.ru       | teacher123')
    print('  teacher  | teacher2@lang.ru       | teacher123')
    for i in range(1, 11):
        print(f'  student  | student{i}@lang.ru        | student123')
    print('=' * 60)
    print()
