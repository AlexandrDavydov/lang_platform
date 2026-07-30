from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from app.views.auth import auth_bp
    from app.views.admin import admin_bp
    from app.views.dashboard import dashboard_bp
    from app.views.materials import materials_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(materials_bp)

    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            role_redirects = {
                'admin': 'admin.dashboard',
                'teacher': 'dashboard.teacher',
                'student': 'dashboard.student',
            }
            return redirect(url_for(role_redirects.get(current_user.role, 'dashboard.student')))
        return redirect(url_for('auth.login'))

    return app
