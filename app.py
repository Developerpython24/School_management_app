from flask import Flask
from datetime import timedelta
import os
import sys
from logging import basicConfig, getLogger
from flask_mail import Mail  # import Flask-Mail

# ریشه پروژه
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

basicConfig(level='INFO')
logger = getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///school_management.db').replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Flask-Mail config
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)

# Imports
from models import db
from routes.general import general_bp
from routes.admin import admin_bp
from routes.teacher import teacher_bp
from init_db import init_db, create_templates

app.register_blueprint(general_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(teacher_bp, url_prefix='/teacher')

db.init_app(app)

# فیکس: startup (gunicorn production) – جدول‌ها و داده‌ها بساز
with app.app_context():
    try:
        db.create_all()  # جدول‌ها رو بساز
        init_db()  # داده‌های نمونه (admin/teacher)
        create_templates()  # تمپلیت‌ها
        logger.info("App initialized successfully. Tables and data ready.")
    except Exception as e:
        logger.error(f"Init error: {e}")
        raise

# فیکس: @before_first_request deprecated – با @before_request و flag first_request جایگزین
first_request = True

@app.before_request
def before_first_request():
    global first_request
    if first_request:
        # فقط اولین request
        with app.app_context():
            try:
                db.create_all()  # double-check tables
                logger.info("First request: Tables ready.")
            except Exception as e:
                logger.error(f"First request error: {e}")
                raise
        first_request = False

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    debug = os.environ.get('ENV') == 'dev'
    logger.info("Server starting on http://127.0.0.1:5000")
    app.run(debug=debug, host=host, port=port)
