from datetime import date, timedelta

FUTURE = (date.today() + timedelta(days=30)).isoformat()


def login(page, base_url, email, password):
    page.goto(f'{base_url}/auth/login')
    page.wait_for_selector('input[name="email"]')
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('input[type="submit"]')


def test_admin_creates_lesson_all_see_it(page, live_server):
    base_url = live_server

    # 1. Admin creates a lesson
    login(page, base_url, 'admin@lang.ru', 'admin123')
    page.wait_for_url(f'{base_url}/admin/dashboard')
    page.goto(f'{base_url}/admin/schedule/{FUTURE}')
    page.wait_for_selector('#student')

    page.select_option('#student', label='Student #1')
    page.select_option('#teacher', label='Teacher #1')
    page.fill('#title', 'E2E Test Lesson')
    page.fill('#start_time', '10:00')
    page.fill('#end_time', '11:00')
    page.click('input[type="submit"]')

    page.wait_for_selector('table')
    assert page.locator('table tbody').filter(has_text='E2E Test Lesson').is_visible()

    # 2. Student sees lesson on dashboard
    page.goto(f'{base_url}/auth/logout')
    login(page, base_url, 'student1@lang.ru', 'student123')
    page.wait_for_url(f'{base_url}/dashboard/student')

    page.wait_for_selector('table')
    assert page.locator('text=E2E Test Lesson').is_visible()

    # 3. Teacher sees lesson on dashboard
    page.goto(f'{base_url}/auth/logout')
    login(page, base_url, 'teacher1@lang.ru', 'teacher123')
    page.wait_for_url(f'{base_url}/dashboard/teacher')

    page.wait_for_selector('table')
    assert page.locator('text=E2E Test Lesson').is_visible()


def test_teacher_creates_lesson_student_admin_see_it(page, live_server):
    base_url = live_server

    # 1. Teacher creates a lesson
    login(page, base_url, 'teacher1@lang.ru', 'teacher123')
    page.wait_for_url(f'{base_url}/dashboard/teacher')
    page.goto(f'{base_url}/dashboard/teacher/schedule/{FUTURE}')
    page.wait_for_selector('#student')

    page.select_option('#student', label='Student #2')
    page.fill('#title', 'Teacher Created Lesson')
    page.fill('#start_time', '14:00')
    page.fill('#end_time', '15:00')
    page.click('input[type="submit"]')

    page.wait_for_selector('table')
    assert page.locator('table tbody').filter(has_text='Teacher Created Lesson').is_visible()

    # 2. Student sees lesson on dashboard
    page.goto(f'{base_url}/auth/logout')
    login(page, base_url, 'student2@lang.ru', 'student123')
    page.wait_for_url(f'{base_url}/dashboard/student')

    page.wait_for_selector('table')
    assert page.locator('text=Teacher Created Lesson').is_visible()

    # 3. Admin sees lesson on schedule page
    page.goto(f'{base_url}/auth/logout')
    login(page, base_url, 'admin@lang.ru', 'admin123')
    page.wait_for_url(f'{base_url}/admin/dashboard')
    page.goto(f'{base_url}/admin/schedule/{FUTURE}')
    page.wait_for_selector('table')

    assert page.locator('table tbody').filter(has_text='Teacher Created Lesson').is_visible()


def test_time_conflict_validation(page, live_server):
    base_url = live_server
    conflict_date = (date.today() + timedelta(days=32)).isoformat()

    login(page, base_url, 'admin@lang.ru', 'admin123')
    page.wait_for_url(f'{base_url}/admin/dashboard')

    # 1. Create initial lesson: Teacher #1 + Student #1 at 10:00-11:00
    page.goto(f'{base_url}/admin/schedule/{conflict_date}')
    page.wait_for_selector('#student')
    page.select_option('#student', label='Student #1')
    page.select_option('#teacher', label='Teacher #1')
    page.fill('#title', 'Initial Lesson')
    page.fill('#start_time', '10:00')
    page.fill('#end_time', '11:00')
    page.click('input[type="submit"]')
    page.wait_for_selector('table')
    assert page.locator('table tbody').filter(has_text='Initial Lesson').is_visible()

    # 2. Try to create overlapping lesson for same Teacher #1 at 10:30-11:30
    page.select_option('#student', label='Student #2')
    page.select_option('#teacher', label='Teacher #1')
    page.fill('#title', 'Teacher Overlap')
    page.fill('#start_time', '10:30')
    page.fill('#end_time', '11:30')
    page.click('input[type="submit"]')
    page.wait_for_selector('.flash')
    assert page.locator('.flash').filter(has_text='Учитель уже занят').is_visible()

    # 3. Try to create overlapping lesson for same Student #1 at 10:30-11:30 with Teacher #2
    page.select_option('#student', label='Student #1')
    page.select_option('#teacher', label='Teacher #2')
    page.fill('#title', 'Student Overlap')
    page.fill('#start_time', '10:30')
    page.fill('#end_time', '11:30')
    page.click('input[type="submit"]')
    page.wait_for_selector('.flash')
    assert page.locator('.flash').filter(has_text='Ученик уже занят').is_visible()

    # 4. Create non-overlapping lesson at 12:00-13:00 with same Teacher #1 + Student #1
    page.select_option('#student', label='Student #1')
    page.select_option('#teacher', label='Teacher #1')
    page.fill('#title', 'Non Overlapping')
    page.fill('#start_time', '12:00')
    page.fill('#end_time', '13:00')
    page.click('input[type="submit"]')
    page.wait_for_selector('table')
    assert page.locator('table tbody').filter(has_text='Non Overlapping').is_visible()
