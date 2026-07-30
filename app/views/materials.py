import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Lesson, Material, User, lesson_materials, lesson_students
from sqlalchemy import and_
from app.forms import LessonForm, MaterialForm
from app.decorators import role_any

materials_bp = Blueprint('materials', __name__, url_prefix='/materials')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    filename = secure_filename(file.filename)
    name, ext = filename.rsplit('.', 1)
    import uuid
    unique = uuid.uuid4().hex[:8]
    saved = f'{name}_{unique}.{ext}'
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved)
    file.save(path)
    return saved


@materials_bp.route('/')
@login_required
@role_any('admin', 'teacher')
def material_list():
    materials = Material.query.order_by(Material.created_at.desc()).all()
    return render_template('materials/list.html', materials=materials)


@materials_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_any('admin', 'teacher')
def material_create():
    form = MaterialForm()
    lesson_id = request.args.get('lesson_id') or request.form.get('lesson_id')
    if form.validate_on_submit():
        file_url = form.file_url.data
        if form.material_type.data == 'image' and request.files.get('image_file'):
            file = request.files['image_file']
            if file and allowed_file(file.filename):
                file_url = save_image(file)

        material = Material(
            title=form.title.data,
            content=form.content.data,
            material_type=form.material_type.data,
            file_url=file_url,
            created_by_id=current_user.id,
        )
        db.session.add(material)
        if lesson_id:
            lesson = db.session.get(Lesson, int(lesson_id))
            if lesson:
                lesson.materials.append(material)
        db.session.commit()
        flash('Материал создан.')
        return redirect(url_for('materials.material_list'))
    return render_template('materials/form.html', form=form, material=None,
                           lesson_id=lesson_id)


@materials_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_any('admin', 'teacher')
def material_edit(id):
    material = db.session.get(Material, id)
    if not material:
        flash('Материал не найден.')
        return redirect(url_for('materials.material_list'))

    form = MaterialForm(obj=material)
    if form.validate_on_submit():
        material.title = form.title.data
        material.content = form.content.data
        material.material_type = form.material_type.data
        file_url = form.file_url.data
        if form.material_type.data == 'image' and request.files.get('image_file'):
            file = request.files['image_file']
            if file and allowed_file(file.filename):
                file_url = save_image(file)
        material.file_url = file_url
        db.session.commit()
        flash('Материал обновлён.')
        return redirect(url_for('materials.material_list'))
    return render_template('materials/form.html', form=form, material=material)


@materials_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_any('admin', 'teacher')
def material_delete(id):
    material = db.session.get(Material, id)
    if material:
        db.session.delete(material)
        db.session.commit()
        flash('Материал удалён.')
    return redirect(url_for('materials.material_list'))


@materials_bp.route('/lessons')
@login_required
def lesson_list():
    if current_user.role == 'student':
        lessons = Lesson.query.filter(Lesson.students.any(id=current_user.id)).order_by(Lesson.created_at.desc()).all()
    else:
        lessons = Lesson.query.order_by(Lesson.created_at.desc()).all()
    return render_template('materials/lessons_list.html', lessons=lessons)


@materials_bp.route('/lessons/create', methods=['GET', 'POST'])
@login_required
@role_any('admin', 'teacher')
def lesson_create():
    form = LessonForm()
    all_students = User.query.filter_by(role='student').all()
    form.students.choices = [(s.id, f'{s.first_name} {s.last_name}') for s in all_students]
    all_materials = Material.query.order_by(Material.title).all()
    form.materials.choices = [(m.id, m.title) for m in all_materials]
    if form.validate_on_submit():
        lesson = Lesson(
            title=form.title.data,
            description=form.description.data,
            created_by_id=current_user.id,
        )
        db.session.add(lesson)
        db.session.flush()
        for s_id in form.students.data:
            s = db.session.get(User, s_id)
            if s:
                lesson.students.append(s)
        for i, m_id in enumerate(form.materials.data):
            m = db.session.get(Material, m_id)
            if m:
                lesson.materials.append(m)
                db.session.execute(
                    lesson_materials.update().where(
                        and_(
                            lesson_materials.c.lesson_id == lesson.id,
                            lesson_materials.c.material_id == m_id,
                        )
                    ).values(order=i)
                )
        db.session.commit()
        flash('Урок создан.')
        return redirect(url_for('materials.lesson_detail', id=lesson.id))
    return render_template('materials/lesson_form.html', form=form, lesson=None, material_orders={})


@materials_bp.route('/lessons/<int:id>')
@login_required
def lesson_detail(id):
    lesson = db.session.get(Lesson, id)
    if not lesson:
        flash('Урок не найден.')
        return redirect(url_for('materials.lesson_list'))
    if current_user.role == 'student' and current_user not in lesson.students:
        flash('У вас нет доступа к этому уроку.')
        return redirect(url_for('materials.lesson_list'))
    materials = lesson.materials.all()
    material_orders = {}
    for m in materials:
        result = db.session.execute(
            lesson_materials.select().where(
                and_(
                    lesson_materials.c.lesson_id == lesson.id,
                    lesson_materials.c.material_id == m.id,
                )
            )
        ).first()
        material_orders[m.id] = result.order if result else 0
    return render_template('materials/lesson_detail.html', lesson=lesson, materials=materials,
                           material_orders=material_orders)


@materials_bp.route('/lessons/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_any('admin', 'teacher')
def lesson_edit(id):
    lesson = db.session.get(Lesson, id)
    if not lesson:
        flash('Урок не найден.')
        return redirect(url_for('materials.lesson_list'))

    form = LessonForm(obj=lesson)
    all_students = User.query.filter_by(role='student').all()
    form.students.choices = [(s.id, f'{s.first_name} {s.last_name}') for s in all_students]
    all_materials = Material.query.order_by(Material.title).all()
    form.materials.choices = [(m.id, m.title) for m in all_materials]
    if form.validate_on_submit():
        lesson.title = form.title.data
        lesson.description = form.description.data
        selected_student_ids = set(form.students.data)
        for s in list(lesson.students.all()):
            if s.id not in selected_student_ids:
                lesson.students.remove(s)
        for s_id in selected_student_ids:
            s = db.session.get(User, s_id)
            if s and s not in lesson.students:
                lesson.students.append(s)
        selected_ids = set(form.materials.data)
        for m in list(lesson.materials.all()):
            if m.id not in selected_ids:
                lesson.materials.remove(m)
        for m_id in selected_ids:
            order = int(request.form.get(f'order_{m_id}', 0))
            m = db.session.get(Material, m_id)
            if m and m not in lesson.materials.all():
                lesson.materials.append(m)
            db.session.execute(
                lesson_materials.update().where(
                    and_(
                        lesson_materials.c.lesson_id == lesson.id,
                        lesson_materials.c.material_id == m_id,
                    )
                ).values(order=order)
            )
        db.session.commit()
        flash('Урок обновлён.')
        return redirect(url_for('materials.lesson_detail', id=lesson.id))
    form.students.data = [s.id for s in lesson.students.all()]
    form.materials.data = [m.id for m in lesson.materials.all()]
    material_orders = {}
    for m in lesson.materials.all():
        result = db.session.execute(
            lesson_materials.select().where(
                and_(
                    lesson_materials.c.lesson_id == lesson.id,
                    lesson_materials.c.material_id == m.id,
                )
            )
        ).first()
        material_orders[m.id] = result.order if result else 0
    return render_template('materials/lesson_form.html', form=form, lesson=lesson,
                           material_orders=material_orders)


@materials_bp.route('/lessons/<int:id>/delete', methods=['POST'])
@login_required
@role_any('admin', 'teacher')
def lesson_delete(id):
    lesson = db.session.get(Lesson, id)
    if lesson:
        lesson.materials = []
        db.session.delete(lesson)
        db.session.commit()
        flash('Урок удалён.')
    return redirect(url_for('materials.lesson_list'))


@materials_bp.route('/lessons/<int:id>/add-material', methods=['GET', 'POST'])
@login_required
@role_any('admin', 'teacher')
def lesson_add_material(id):
    lesson = db.session.get(Lesson, id)
    if not lesson:
        flash('Урок не найден.')
        return redirect(url_for('materials.lesson_list'))

    existing_ids = {m.id for m in lesson.materials.all()}
    other_materials = Material.query.filter(~Material.id.in_(existing_ids)).order_by(Material.title).all() if existing_ids else Material.query.order_by(Material.title).all()

    if request.method == 'POST':
        material_id = request.form.get('material_id')
        material = db.session.get(Material, int(material_id))
        if material and material not in lesson.materials.all():
            max_order = db.session.execute(
                db.select(db.func.coalesce(db.func.max(lesson_materials.c.order), -1)).where(
                    lesson_materials.c.lesson_id == lesson.id
                )
            ).scalar()
            lesson.materials.append(material)
            db.session.execute(
                lesson_materials.update().where(
                    and_(
                        lesson_materials.c.lesson_id == lesson.id,
                        lesson_materials.c.material_id == material.id,
                    )
                ).values(order=max_order + 1)
            )
            db.session.commit()
            flash(f'Материал "{material.title}" добавлен в урок.')
        return redirect(url_for('materials.lesson_detail', id=lesson.id))

    return render_template('materials/add_material.html', lesson=lesson, materials=other_materials)


@materials_bp.route('/lessons/<int:id>/remove-material/<int:material_id>', methods=['POST'])
@login_required
@role_any('admin', 'teacher')
def lesson_remove_material(id, material_id):
    lesson = db.session.get(Lesson, id)
    material = db.session.get(Material, material_id)
    if lesson and material:
        lesson.materials.remove(material)
        db.session.commit()
        flash('Материал удалён из урока.')
    return redirect(url_for('materials.lesson_detail', id=id))
