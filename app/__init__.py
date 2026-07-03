import os
from flask import Flask, render_template, redirect, url_for
from config import config


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    _init_extensions(app)
    _register_blueprints(app)
    _register_login_loader(app)
    _register_before_request(app)

    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('chat.rooms'))
        from app.auth.forms import LoginForm
        form = LoginForm()
        return render_template('auth/login.html', form=form, title='Log In')

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    return app


def _init_extensions(app):
    from app.extensions import db, migrate, login_manager, socketio, csrf  
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(
        app,
        message_queue=app.config.get('SOCKETIO_MESSAGE_QUEUE') or None,
        logger=False,
        engineio_logger=False,
    )
    csrf.init_app(app)

def _register_blueprints(app):
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.chat import chat_bp
    app.register_blueprint(chat_bp, url_prefix='/chat')   

    from app.friends import friends_bp                    
    app.register_blueprint(friends_bp, url_prefix='/friends')

    from app.profile import profile_bp
    app.register_blueprint(profile_bp, url_prefix='/profile')

    from app.chat import events  


def _register_login_loader(app):
    from app.extensions import login_manager
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db_load_user(user_id)

    def db_load_user(user_id):
        from app.extensions import db
        return db.session.get(User, int(user_id))


def _register_before_request(app):
    from flask_login import current_user
    from app.extensions import db

    @app.before_request
    def update_last_seen():
        if current_user.is_authenticated:
            current_user.ping()
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()