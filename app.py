from flask import Flask
from datetime import timedelta
import os
import sys
from logging import basicConfig, getLogger

# فیکس: ریشه پروژه رو اولویت بده
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Logging
basicConfig(level='INFO')
logger = getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Imports
from models import db
from routes.general import general_bp
from routes.admin import admin_bp
from routes.teacher import teacher_bp
from init_db import init_db, create_templates

# Register blueprints
app.register_blueprint(general_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(teacher_bp, url_prefix='/teacher')

if __name__ == '__main__':
    db.init_app(app)
    with app.app_context():
        try:
            init_db()
            create_templates()
            logger.info("App initialized successfully. Server starting on http://127.0.0.1:5000")
        except Exception as e:
            logger.error(f"Init error: {e}")
            raise
    app.run(debug=True)