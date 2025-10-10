
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from models import db, Admin, Teacher
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Message  # فیکس: import Message
from itsdangerous import URLSafeTimedSerializer  # pip install itsdangerous

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
        
        # فیکس: Automatic create if not exist (first-time setup)
        if role == 'admin':
            admin = Admin.query.filter_by(username=username).first()
            if not admin:
                # اگر admin وجود نداره، بساز
                admin = Admin(
                    username='admin',  # default
                    password_hash=generate_password_hash('admin123'),  # default رمز
                    school_name='مدرسه راهنمایی نمونه',
                    principal_name='محمد محمدی'
                )
                db.session.add(admin)
                db.session.commit()
                flash('ادمین پیش‌فرض ساخته شد (username: admin, password: admin123). لطفاً لاگین کنید.', 'success')
                return redirect(url_for('general.login'))
            if check_password_hash(admin.password_hash, password):
                session['user_id'] = admin.id
                session['username'] = admin.username
                session['role'] = 'admin'
                session.permanent = True
                return redirect(url_for('admin.admin_dashboard'))
        else:
            teacher = Teacher.query.filter_by(username=username).first()
            if not teacher:
                # اگر teacher وجود نداره، بساز
                teacher = Teacher(
                    username='teacher',  # default
                    password_hash=generate_password_hash('teacher123'),  # default رمز
                    first_name='علی',
                    last_name='احمدی'
                )
                db.session.add(teacher)
                db.session.commit()
                flash('معلم پیش‌فرض ساخته شد (username: teacher, password: teacher123). لطفاً لاگین کنید.', 'success')
                return redirect(url_for('general.login'))
            if check_password_hash(teacher.password_hash, password):
                session['user_id'] = teacher.id
                session['username'] = teacher.username
                session['role'] = 'teacher'
                session['teacher_name'] = f"{teacher.first_name} {teacher.last_name}"
                session.permanent = True
                return redirect(url_for('teacher.teacher_dashboard'))
        
        flash('نام کاربری یا رمز عبور اشتباه است', 'error')
    return render_template('login.html')
@general_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        role = request.form.get('role')
        if role == 'admin':
            user = Admin.query.filter_by(username=username).first()
        else:
            user = Teacher.query.filter_by(username=username).first()
        if user and user.email:  # فرض: فیلد email در مدل‌ها (اگر نداری، username استفاده کن)
            s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
            token = s.dumps(username, salt='password-reset')
            link = url_for('general.reset_password', token=token, _external=True)
            msg = Message('Reset Password', sender=app.config['MAIL_USERNAME'], recipients=[user.email])
            msg.body = f'Click this link to reset password: {link}. Expires in 1 hour.'
            mail.send(msg)
            flash('لینک reset به ایمیل ارسال شد', 'success')
        else:
            flash('کاربر یافت نشد یا ایمیل ثبت نشده', 'error')
        return redirect(url_for('general.login'))
    return render_template('forgot_password.html')

@general_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        username = s.loads(token, salt='password-reset', max_age=3600)  # 1 hour expiry
    except:
        flash('لینک نامعتبر یا منقضی شده', 'error')
        return redirect(url_for('general.login'))
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if len(new_password) < 6:
            flash('رمز عبور حداقل 6 کاراکتر باشد', 'error')
            return render_template('reset_password.html', token=token, username=username)
        if new_password != confirm_password:
            flash('رمز عبور و تأیید مطابقت ندارد', 'error')
            return render_template('reset_password.html', token=token, username=username)
        if username.startswith('admin'):  # admin
            admin = Admin.query.filter_by(username=username).first()
            admin.password_hash = generate_password_hash(new_password)
        else:  # teacher
            teacher = Teacher.query.filter_by(username=username).first()
            teacher.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('رمز عبور تغییر یافت', 'success')
        return redirect(url_for('general.login'))
    return render_template('reset_password.html', token=token, username=username)
@general_bp.route('/logout')
def logout():
    session.clear()
    flash('با موفقیت خارج شدید', 'success')
    return redirect(url_for('general.login'))
