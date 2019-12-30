"""Flask config class."""
import os


class Config:
    """Set Flask configuration vars."""

    # General Config
    TESTING = os.environ.get('TESTING')
    DEBUG = os.environ.get('DEBUG')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME')
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    logfile = '%s.log' % __name__
    JWT_ACCESS_TOKEN_EXPIRES = False
    JWT_TOKEN_LOCATION = 'headers'
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'secret_key')
