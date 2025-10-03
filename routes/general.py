from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from models import db, Admin, Teacher
from werkzeug.security import check_password_hash

general_bp = Blueprint('general', __name__)

def login_required(role='any'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('لطفا وارد شوید', 'error')
                return redirect(url_for('general.login'))
            if role == 'admin' and session.get('role') != 'admin':
                flash('دسترسی محدود به ادمین', 'error')
                return redirect(url_for('general.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@general_bp.route('/')
def index():
    return render_template('index.html')

@general_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        if role == 'admin':
            admin = Admin.query.filter_by(username=username).first()
            if admin and check_password_hash(admin.password_hash, password):
                session['user_id'] = admin.id
                session['username'] = admin.username
                session['role'] = 'admin'
                session.permanent = True
                return redirect(url_for('admin.admin_dashboard'))
        else:
            teacher = Teacher.query.filter_by(username=username).first()
            if teacher and check_password_hash(teacher.password_hash, password):
                session['user_id'] = teacher.id
                session['username'] = teacher.username
                session['role'] = 'teacher'
                session['teacher_name'] = f"{teacher.first_name} {teacher.last_name}"
                session.permanent = True
                return redirect(url_for('teacher.teacher_dashboard'))
        flash('نام کاربری یا رمز عبور اشتباه است', 'error')
    return render_template('login.html')

@general_bp.route('/logout')
def logout():
    session.clear()
    flash('با موفقیت خارج شدید', 'success')
    return redirect(url_for('general.login'))