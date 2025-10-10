from flask import Flask
from datetime import timedelta
import os
import sys
from logging import basicConfig, getLogger

# ریشه پروژه
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

basicConfig(level='INFO')
logger = getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///school_management.db').replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

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

# فیکس: create_all در startup (قبل __main__, برای production)
with app.app_context():
    db.create_all()  # جدول‌ها رو بساز (idempotent، همیشه OK)
    if os.environ.get('ENV') == 'dev':
        init_db()  # داده‌های نمونه فقط dev
        create_templates()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    debug = os.environ.get('ENV') == 'dev'
    logger.info("App initialized successfully. Server starting on http://127.0.0.1:5000")
    app.run(debug=debug, host=host, port=port)
