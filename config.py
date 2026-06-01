import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Absolute path to SQLite database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'reelwrapped.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads folder absolute path
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Admin PIN for authentication
    ADMIN_PIN = os.environ.get('ADMIN_PIN') or '0987654321qwerty'
