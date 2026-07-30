import uuid


def login(page, base_url, email, password):
    page.goto(f'{base_url}/auth/login')
    page.wait_for_selector('input[name="email"]')
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('input[type="submit"]')


def create_text_material(page, base_url, title, content):
    page.goto(f'{base_url}/materials/create')
    page.wait_for_selector('#title')
    page.fill('#title', title)
    page.select_option('#material_type', 'text')
    page.wait_for_timeout(100)
    page.fill('textarea[name="content"]', content)
    page.click('input[type="submit"]')
    page.wait_for_url(f'{base_url}/materials/')


def create_link_material(page, base_url, title, url):
    page.goto(f'{base_url}/materials/create')
    page.wait_for_selector('#title')
    page.fill('#title', title)
    page.select_option('#material_type', 'link')
    page.wait_for_timeout(100)
    page.fill('#file_url', url)
    page.click('input[type="submit"]')
    page.wait_for_url(f'{base_url}/materials/')


def create_lesson(page, base_url, title, description, student_labels, material_titles):
    page.goto(f'{base_url}/materials/lessons/create')
    page.wait_for_selector('input[name="title"]')
    page.fill('input[name="title"]', title)
    page.fill('textarea[name="description"]', description)

    for label in student_labels:
        page.check(f'table >> tr:has(td:text("{label}")) >> input[type="checkbox"]')

    for mat_title in material_titles:
        page.check(f'table >> tr:has(td:text("{mat_title}")) >> input[type="checkbox"]')

    page.click('input[type="submit"]')
    page.wait_for_url(f'{base_url}/materials/lessons/*')


SUFFIX = uuid.uuid4().hex[:6]


def test_admin_creates_materials_and_lesson_student_sees_it(page, live_server):
    base_url = live_server

    login(page, base_url, 'admin@lang.ru', 'admin123')

    create_text_material(page, base_url, f'Text Mat {SUFFIX}', f'Hello from {SUFFIX}')
    create_link_material(page, base_url, f'Link Mat {SUFFIX}', f'https://example.com/{SUFFIX}')

    create_lesson(page, base_url, f'Lesson {SUFFIX}', f'Desc {SUFFIX}',
                  ['Student #1'], [f'Text Mat {SUFFIX}', f'Link Mat {SUFFIX}'])

    assert page.locator(f'h1:has-text("Lesson {SUFFIX}")').is_visible()
    assert page.locator(f'text=Hello from {SUFFIX}').is_visible()
    assert page.locator(f'text=https://example.com/{SUFFIX}').is_visible()

    page.goto(f'{base_url}/auth/logout')
    login(page, base_url, 'student1@lang.ru', 'student123')
    page.wait_for_url(f'{base_url}/dashboard/student')
    assert page.locator(f'text=Lesson {SUFFIX}').is_visible()

    page.click(f'a[href*="/materials/lessons/"]:has-text("Открыть")')
    page.wait_for_selector(f'h1:has-text("Lesson {SUFFIX}")')
    assert page.locator(f'text=Hello from {SUFFIX}').is_visible()
    assert page.locator(f'text=https://example.com/{SUFFIX}').is_visible()


def test_teacher_creates_lesson_assigned_student_sees_unassigned_does_not(page, live_server):
    base_url = live_server
    suf = uuid.uuid4().hex[:6]

    login(page, base_url, 'teacher1@lang.ru', 'teacher123')

    create_text_material(page, base_url, f'Teacher Mat {suf}', f'Content {suf}')

    create_lesson(page, base_url, f'Teacher Lesson {suf}', f'Desc {suf}',
                  ['Student #3'], [f'Teacher Mat {suf}'])

    page.goto(f'{base_url}/auth/logout')
    login(page, base_url, 'student3@lang.ru', 'student123')
    page.wait_for_url(f'{base_url}/dashboard/student')
    assert page.locator(f'text=Teacher Lesson {suf}').is_visible()

    page.goto(f'{base_url}/auth/logout')
    login(page, base_url, 'student5@lang.ru', 'student123')
    page.wait_for_url(f'{base_url}/dashboard/student')
    assert page.locator(f'text=Teacher Lesson {suf}').is_hidden()


def test_student_cannot_access_unassigned_lesson_by_url(page, live_server):
    base_url = live_server
    suf = uuid.uuid4().hex[:6]

    login(page, base_url, 'admin@lang.ru', 'admin123')

    create_text_material(page, base_url, f'Restrict Mat {suf}', f'Secret {suf}')
    create_lesson(page, base_url, f'Restricted Lesson {suf}', f'Secret lesson {suf}',
                  ['Student #1'], [f'Restrict Mat {suf}'])

    lesson_url = page.url

    page.goto(f'{base_url}/auth/logout')
    login(page, base_url, 'student2@lang.ru', 'student123')
    page.wait_for_url(f'{base_url}/dashboard/student')

    page.goto(lesson_url)
    page.wait_for_timeout(300)
    assert page.locator('.flash:has-text("Нет доступа")').is_visible() or \
           page.locator(f'text=Restricted Lesson {suf}').is_hidden()


def test_edit_lesson_add_student_and_remove_material(page, live_server):
    base_url = live_server
    suf = uuid.uuid4().hex[:6]

    login(page, base_url, 'admin@lang.ru', 'admin123')

    create_text_material(page, base_url, f'Edit Mat A {suf}', f'Keep me {suf}')
    create_text_material(page, base_url, f'Edit Mat B {suf}', f'Remove me {suf}')

    create_lesson(page, base_url, f'Edit Lesson {suf}', f'Edit desc {suf}',
                  ['Student #1'], [f'Edit Mat A {suf}', f'Edit Mat B {suf}'])
    assert page.locator(f'text=Keep me {suf}').is_visible()
    assert page.locator(f'text=Remove me {suf}').is_visible()

    page.click('a:has-text("Редактировать урок")')
    page.wait_for_selector('input[name="title"]')

    page.check(f'table >> tr:has(td:text("Student #2")) >> input[type="checkbox"]')

    page.uncheck(f'table >> tr:has(td:text("Edit Mat B {suf}")) >> input[type="checkbox"]')

    page.click('input[type="submit"]')
    page.wait_for_selector(f'h1:has-text("Edit Lesson {suf}")')
    assert page.locator(f'text=Keep me {suf}').is_visible()
    assert page.locator(f'text=Remove me {suf}').is_hidden()

    page.goto(f'{base_url}/auth/logout')
    login(page, base_url, 'student2@lang.ru', 'student123')
    page.wait_for_url(f'{base_url}/dashboard/student')
    assert page.locator(f'text=Edit Lesson {suf}').is_visible()


def test_material_shared_across_multiple_lessons(page, live_server):
    base_url = live_server
    suf = uuid.uuid4().hex[:6]

    login(page, base_url, 'admin@lang.ru', 'admin123')

    create_text_material(page, base_url, f'Shared Mat {suf}', f'Shared content {suf}')

    create_lesson(page, base_url, f'Lesson A {suf}', f'First {suf}',
                  ['Student #1'], [f'Shared Mat {suf}'])
    page.wait_for_selector(f'h1:has-text("Lesson A {suf}")')
    assert page.locator(f'text=Shared content {suf}').is_visible()

    page.goto(f'{base_url}/materials/lessons/create')
    page.wait_for_selector('input[name="title"]')
    page.fill('input[name="title"]', f'Lesson B {suf}')
    page.fill('textarea[name="description"]', f'Second {suf}')
    page.check(f'table >> tr:has(td:text("Student #2")) >> input[type="checkbox"]')
    page.check(f'table >> tr:has(td:text("Shared Mat {suf}")) >> input[type="checkbox"]')
    page.click('input[type="submit"]')
    page.wait_for_selector(f'h1:has-text("Lesson B {suf}")')
    assert page.locator(f'text=Shared content {suf}').is_visible()

    page.goto(f'{base_url}/auth/logout')
    login(page, base_url, 'student1@lang.ru', 'student123')
    page.wait_for_url(f'{base_url}/dashboard/student')
    page.click(f'a[href*="/materials/lessons/"]:has-text("Открыть")')
    page.wait_for_timeout(300)

    page.goto(f'{base_url}/auth/logout')
    login(page, base_url, 'student2@lang.ru', 'student123')
    page.wait_for_url(f'{base_url}/dashboard/student')
    assert page.locator(f'text=Lesson B {suf}').is_visible()
