import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-key-that-maybe-will-not-change-cuz-im-lazy'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'chatapp.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # photo settings
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    
    SOCKETIO_MESSAGE_QUEUE = os.environ.get('SOCKETIO_MESSAGE_QUEUE') or ''
    
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    @classmethod
    def init_app(cls, app):
      Config.init_app(app) if hasattr(Config, 'init_app') else None
      assert os.environ.get('SECRET_KEY'), 'SECRET_KEY environment variable not set!'
      assert os.environ.get('DATABASE_URL'), 'DATABASE_URL environment variable not set!'
      
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}  
    