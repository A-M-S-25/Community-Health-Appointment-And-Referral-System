import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


def get_database_uri():
    mysql_url = os.getenv('DATABASE_URL')
    if mysql_url:
        return mysql_url

    mysql_user = os.getenv('MYSQL_USER')
    if mysql_user:
        host = os.getenv('MYSQL_HOST', 'localhost')
        port = os.getenv('MYSQL_PORT', '3306')
        db_name = os.getenv('MYSQL_DATABASE', 'charsystem')
        password = os.getenv('MYSQL_PASSWORD', '')
        return f'mysql+pymysql://{mysql_user}:{password}@{host}:{port}/{db_name}'

    return f'sqlite:///{BASE_DIR / "charsystem.db"}'


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'charsystem-dev-secret')
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SMS_API_URL = os.getenv('SMS_API_URL', '')
    SMS_API_KEY = os.getenv('SMS_API_KEY', 'demo-sms-key')
    APP_ENV = os.getenv('APP_ENV', 'development')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
