import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def get_mysql_connection():
    host = os.getenv('MYSQL_HOST', 'localhost')
    port = int(os.getenv('MYSQL_PORT', '3306'))
    user = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD', '')
    database = os.getenv('MYSQL_DATABASE', 'charsystem')

    if not user:
        raise RuntimeError('MYSQL_USER is not defined. Set MySQL credentials in .env before running migrations.')

    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        autocommit=True,
    )


def apply_mysql_schema():
    schema_path = BASE_DIR / 'migrations' / 'schema.sql'
    sql = schema_path.read_text(encoding='utf-8')

    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            for statement in sql.split(';'):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
            cursor.execute(
                'ALTER TABLE facilities MODIFY contact_info JSON NOT NULL'
            )
            for statement in (
                'ALTER TABLE facilities ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE',
                'ALTER TABLE healthcare_workers ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE',
                'ALTER TABLE healthcare_workers ADD COLUMN last_login_at DATETIME NULL',
                'ALTER TABLE referrals ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP',
                'ALTER TABLE appointments MODIFY referral_id INT UNSIGNED NULL',
                'ALTER TABLE appointments ADD COLUMN patient_id INT UNSIGNED NULL',
                'ALTER TABLE appointments ADD CONSTRAINT fk_appointments_patient FOREIGN KEY (patient_id) REFERENCES patients (patient_id)',
            ):
                try:
                    cursor.execute(statement)
                except pymysql.err.OperationalError as exc:
                    if exc.args and exc.args[0] not in (1060, 1826):
                        raise
        print(f'MySQL schema applied to {os.getenv("MYSQL_DATABASE", "charsystem")} successfully.')
    finally:
        conn.close()


if __name__ == '__main__':
    apply_mysql_schema()
