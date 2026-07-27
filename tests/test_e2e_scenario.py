import pytest


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
    page.goto(f'{base_url}/admin/schedule/2026-07-26')
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
