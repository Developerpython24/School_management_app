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
# فیکس: DB URI از env (Render DATABASE_URL set می‌کنه)
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

# فیکس: init_db فقط dev
if os.environ.get('ENV') == 'dev':
    with app.app_context():
        init_db()
        create_templates()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'  # فیکس: bind to all interfaces for Render
    debug = os.environ.get('ENV') == 'dev'
    app.run(debug=debug, host=host, port=port)
