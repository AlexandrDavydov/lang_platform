from app import create_app, db
from app.models import User, Lesson, Material, lesson_materials, lesson_students
from sqlalchemy import and_

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

    teacher1 = User.query.filter_by(username='teacher1').first()
    teacher2 = User.query.filter_by(username='teacher2').first()
    student1 = User.query.filter_by(username='student1').first()

    materials = [
        Material(title='Алфавит', content='A, B, C, D, E, F, G…', material_type='text', created_by_id=teacher1.id),
        Material(title='Правила чтения', content='Базовые правила произношения букв и буквосочетаний.', material_type='text', created_by_id=teacher1.id),
        Material(title='Словарь 100 слов', file_url='https://example.com/100words.pdf', material_type='link', created_by_id=teacher2.id),
        Material(title='Грамматика: Present Simple', content='I work, he works… Образование и употребление.', material_type='text', created_by_id=teacher1.id),
        Material(title='Карта мира', material_type='image', created_by_id=teacher2.id),
        Material(title='Неправильные глаголы', file_url='https://example.com/irregular-verbs.pdf', material_type='link', created_by_id=teacher1.id),
    ]
    db.session.add_all(materials)
    db.session.flush()

    student2 = User.query.filter_by(username='student2').first()

    lesson1 = Lesson(
        title='Вводный урок',
        description='Знакомство с алфавитом и базовыми правилами чтения.',
        created_by_id=teacher1.id,
    )
    db.session.add(lesson1)
    db.session.flush()
    lesson1.students.append(student1)
    lesson1.students.append(student2)
    for i, m in enumerate([materials[0], materials[1], materials[4]]):
        lesson1.materials.append(m)
        db.session.execute(
            lesson_materials.update().where(
                and_(
                    lesson_materials.c.lesson_id == lesson1.id,
                    lesson_materials.c.material_id == m.id,
                )
            ).values(order=i)
        )

    lesson2 = Lesson(
        title='Основы грамматики',
        description='Present Simple и первые 100 слов.',
        created_by_id=teacher1.id,
    )
    db.session.add(lesson2)
    db.session.flush()
    lesson2.students.append(student1)
    lesson2.students.append(student2)
    for i, m in enumerate([materials[3], materials[2], materials[5]]):
        lesson2.materials.append(m)
        db.session.execute(
            lesson_materials.update().where(
                and_(
                    lesson_materials.c.lesson_id == lesson2.id,
                    lesson_materials.c.material_id == m.id,
                )
            ).values(order=i)
        )

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
