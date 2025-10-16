
import textwrap

from models import db, Admin, Teacher, Grade, Class, TeacherClass
from werkzeug.security import generate_password_hash
import os

def init_db():
    try:
        # فیکس: بدون db.app.app_context() – session مستقیم
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                school_name='مدرسه راهنمایی نمونه',
                principal_name='محمد محمدی'
            )
            db.session.add(admin)
            db.session.flush()
            print("Admin added")
        else:
            print("Admin already exists")

        grades = ['هفتم', 'هشتم', 'نهم']
        for grade_name in grades:
            if not Grade.query.filter_by(name=grade_name).first():
                grade = Grade(name=grade_name)
                db.session.add(grade)
        db.session.flush()

        class_names = ['توحید', 'نبوت', 'معاد']
        for grade in Grade.query.all():
            for cname in class_names:
                cls_name = f"{grade.name} {cname}"
                if not Class.query.filter_by(name=cls_name).first():
                    cls = Class(name=cls_name, grade_id=grade.id)
                    db.session.add(cls)
        db.session.flush()

        if not Teacher.query.filter_by(username='teacher').first():
            teacher = Teacher(
                username='teacher',
                password_hash=generate_password_hash('teacher123'),
                first_name='علی',
                last_name='احمدی'
            )
            db.session.add(teacher)
            db.session.flush()
            tc = TeacherClass(teacher_id=teacher.id, class_id=Class.query.first().id)
            db.session.add(tc)
            db.session.commit()
            print("Teacher added")
        else:
            print("Teacher already exists")

        print("Database initialized successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Init DB error: {e}")
        raise e
def create_templates():
    templates_dir = 'templates'
    os.makedirs(templates_dir, exist_ok=True)
    templates = {
        'base.html': '''\
            <!DOCTYPE html>
            <html lang="fa" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{% block title %}سیستم مدیریت مدرسه{% endblock %}</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
                <style>
                    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/font-face.css');
                    body { font-family: 'Vazir', sans-serif; background-color: #f8f9fa; }
                    .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
                    .card { border: none; box-shadow: 0 0 20px rgba(0,0,0,0.1); border-radius: 15px; }
                    .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; }
                    .btn-primary:hover { background: linear-gradient(135deg, #764ba2 0%, #667eea 100%); }
                    .footer-buttons { background-color: #f8f9fa; padding: 20px 0; margin-top: 40px; border-top: 1px solid #dee2e6; }
                </style>
            </head>
            <body>
                {% if session.get('user_id') %}
                <nav class="navbar navbar-expand-lg navbar-dark">
                    <div class="container">
                        <a class="navbar-brand" href="#">
                            <i class="bi bi-mortarboard-fill"></i> سیستم مدیریت مدرسه
                        </a>
                        <div class="navbar-nav ms-auto">
                            <span class="navbar-text text-white me-3">
                                خوش آمدید، {{ session.get('username') }}
                            </span>
                            <a class="btn btn-outline-light btn-sm" href="{{ url_for('general.logout') }}">
                                <i class="bi bi-box-arrow-right"></i> خروج
                            </a>
                        </div>
                    </div>
                </nav>
                {% endif %}
            
                <div class="container mt-4">
                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                                    {{ message }}
                                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                </div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                
                    {% block content %}{% endblock %}
                </div>

                <!-- فیکس: دکمه‌های بازگشت (در footer، برای همه صفحات) -->
                {% if session.get('user_id') %}
                <footer class="footer-buttons">
                    <div class="container">
                        <div class="row justify-content-center">
                            <div class="col-auto">
                                <a href="{{ request.referrer or url_for('general.index') }}" class="btn btn-secondary me-2">
                                    <i class="bi bi-arrow-left"></i> بازگشت به صفحه قبل
                                </a>
                                <a href="{{ url_for('admin.admin_dashboard') if session.get('role') == 'admin' else url_for('teacher.teacher_dashboard') }}" class="btn btn-primary">
                                    <i class="bi bi-house-door"></i> صفحه اصلی (داشبورد)
                                </a>
                            </div>
                        </div>
                    </div>
                </footer>
                {% endif %}
            
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                {% block scripts %}{% endblock %}
            </body>
            </html>''',
        'index.html': textwrap.dedent('''\
            {% extends "base.html" %}
            {% block content %}
            <div class="row justify-content-center mt-5">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body text-center py-5">
                            <h1 class="display-4 mb-4">
                                <i class="bi bi-mortarboard-fill text-primary"></i>
                            </h1>
                            <h2>سیستم مدیریت مدرسه</h2>
                            <p class="text-muted">سیستم یکپارچه ثبت نمرات و پیشرفت تحصیلی</p>
                            <a href="{{ url_for('general.login') }}" class="btn btn-primary btn-lg mt-3">
                                <i class="bi bi-box-arrow-in-right"></i> ورود به سیستم
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            {% endblock %}'''),
       'login.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <div class="row justify-content-center mt-5">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body p-4">
                            <h3 class="text-center mb-4">ورود به سیستم</h3>
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">نوع کاربری</label>
                                    <select name="role" class="form-select" required>
                                        <option value="admin">مدیر سیستم</option>
                                        <option value="teacher">معلم</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">نام کاربری</label>
                                    <input type="text" name="username" class="form-control" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">رمز عبور</label>
                                    <input type="password" name="password" class="form-control" required>
                                </div>
                                <div class="mb-3 form-check">
                                    <input type="checkbox" name="first_time" class="form-check-input" id="first_time">
                                    <label class="form-check-label" for="first_time">اولین بار (ساخت پیش‌فرض)</label>
                                </div>
                                <button type="submit" class="btn btn-primary w-100 mb-2">
                                    <i class="bi bi-box-arrow-in-right"></i> ورود
                                </button>
                            </form>
                            <a href="{{ url_for('general.forgot_password') }}" class="text-center d-block mt-2 text-primary">
                                <small>فراموشی رمز عبور؟</small>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            {% endblock %}''',

        'forgot_password.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <div class="row justify-content-center mt-5">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body p-4">
                            <h3 class="text-center mb-4">فراموشی رمز عبور</h3>
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">نوع کاربری</label>
                                    <select name="role" class="form-select" required>
                                        <option value="admin">مدیر سیستم</option>
                                        <option value="teacher">معلم</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">نام کاربری</label>
                                    <input type="text" name="username" class="form-control" required>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">
                                    <i class="bi bi-envelope"></i> ارسال لینک
                                </button>
                            </form>
                            <a href="{{ url_for('general.login') }}" class="text-center d-block mt-2">
                                <small>بازگشت به ورود</small>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            {% endblock %}''',
        
        'reset_password.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <div class="row justify-content-center mt-5">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body p-4">
                            <h3 class="text-center mb-4">تغییر رمز عبور</h3>
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">نام کاربری</label>
                                    <input type="text" name="username" value="{{ username }}" class="form-control" readonly>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">رمز عبور جدید</label>
                                    <input type="password" name="new_password" class="form-control" minlength="6" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">تأیید رمز عبور</label>
                                    <input type="password" name="confirm_password" class="form-control" minlength="6" required>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">
                                    <i class="bi bi-lock"></i> تغییر رمز
                                </button>
                            </form>
                            <a href="{{ url_for('general.login') }}" class="text-center d-block mt-2">
                                <small>بازگشت به ورود</small>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            {% endblock %}''',
        'admin_dashboard.html': textwrap.dedent('''\
            {% extends "base.html" %}
            {% block content %}
            <div class="row">
                <div class="col-md-12">
                    <h2 class="mb-4">داشبورد مدیر</h2>
                    <div class="card mb-4">
                        <div class="card-body">
                            <h5>نام مدرسه: {{ admin.school_name }}</h5>
                            <h5>نام مدیر: {{ admin.principal_name }}</h5>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card text-center">
                                <div class="card-body">
                                    <i class="bi bi-people-fill display-4 text-primary"></i>
                                    <h5>تعداد دانش آموزان</h5>
                                    <h3>{{ students_count }}</h3>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card text-center">
                                <div class="card-body">
                                    <i class="bi bi-person-badge-fill display-4 text-primary"></i>
                                    <h5>تعداد معلمان</h5>
                                    <h3>{{ teachers_count }}</h3>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card text-center">
                                <div class="card-body">
                                    <i class="bi bi-building display-4 text-primary"></i>
                                    <h5>تعداد کلاس ها</h5>
                                    <h3>{{ classes_count }}</h3>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="mt-4">
                        <a href="{{ url_for('admin.admin_settings') }}" class="btn btn-primary me-2"><i class="bi bi-gear"></i> تنظیمات</a>
                        <a href="{{ url_for('admin.manage_grades') }}" class="btn btn-primary me-2"><i class="bi bi-layers"></i> مدیریت پایه ها</a>
                        <a href="{{ url_for('admin.manage_classes') }}" class="btn btn-primary me-2"><i class="bi bi-building"></i> مدیریت کلاس ها</a>
                        <a href="{{ url_for('admin.manage_teachers') }}" class="btn btn-primary me-2"><i class="bi bi-person-badge"></i> مدیریت معلمان</a>
                        <a href="{{ url_for('admin.manage_students') }}" class="btn btn-primary me-2"><i class="bi bi-people"></i> مدیریت دانش آموزان</a>
                        <a href="{{ url_for('admin.manage_subjects') }}" class="btn btn-primary me-2"><i class="bi bi-book"></i> مدیریت دروس</a>
                        <a href="{{ url_for('admin.admin_attendance') }}" class="btn btn-primary me-2"><i class="bi bi-check-circle"></i> حضورغیاب</a>
                        <a href="{{ url_for('admin.admin_discipline') }}" class="btn btn-primary me-2"><i class="bi bi-exclamation-triangle"></i> بی‌انضباطی</a>
                        <a href="{{ url_for('admin.reports') }}" class="btn btn-primary"><i class="bi bi-graph-up"></i> گزارش ها</a>
                    </div>
                </div>
            </div>
            {% endblock %}'''),
        'admin_settings.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>تنظیمات مدیر</h2>
            <form method="POST">
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label>نام کاربری (قابل تغییر)</label>
                            <input type="text" name="username" class="form-control" value="{{ admin.username }}" required>
                        </div>
                        <div class="mb-3">
                            <label>رمز عبور جدید (خالی بگذارید برای بدون تغییر)</label>
                            <input type="password" name="new_password" class="form-control" minlength="6">
                        </div>
                        <div class="mb-3">
                            <label>تأیید رمز عبور جدید</label>
                            <input type="password" name="confirm_password" class="form-control" minlength="6">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label>نام مدرسه</label>
                            <input type="text" name="school_name" class="form-control" value="{{ admin.school_name }}" required>
                        </div>
                        <div class="mb-3">
                            <label>نام مدیر</label>
                            <input type="text" name="principal_name" class="form-control" value="{{ admin.principal_name }}" required>
                        </div>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">ذخیره</button>
            </form>
            {% endblock %}''',
        'manage_grades.html': textwrap.dedent('''\
            {% extends "base.html" %}
            {% block content %}
            <h2>مدیریت پایه های تحصیلی</h2>
            <form method="POST" action="{{ url_for('admin.add_grade') }}">
                <div class="input-group mb-3">
                    <input type="text" name="name" class="form-control" placeholder="نام پایه (مثل هفتم)" required>
                    <button type="submit" class="btn btn-primary">اضافه کردن</button>
                </div>
            </form>
            <table class="table">
                <thead>
                    <tr><th>نام</th><th>عملیات</th></tr>
                </thead>
                <tbody>
                    {% for grade in grades %}
                    <tr>
                        <td>{{ grade.name }}</td>
                        <td>
                            <form method="POST" action="{{ url_for('admin.edit_grade', grade_id=grade.id) }}" class="d-inline">
                                <input type="text" name="name" value="{{ grade.name }}" class="form-control d-inline w-auto" style="width:100px;">
                                <button type="submit" class="btn btn-sm btn-warning">ویرایش</button>
                            </form>
                            <a href="{{ url_for('admin.delete_grade', grade_id=grade.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('حذف شود؟')">حذف</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endblock %}'''),
        'manage_classes.html': textwrap.dedent('''\
            {% extends "base.html" %}
            {% block content %}
            <h2>مدیریت کلاس ها</h2>
            <form method="POST" action="{{ url_for('admin.add_class') }}">
                <div class="mb-3">
                    <label>نام کلاس</label>
                    <input type="text" name="name" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label>پایه</label>
                    <select name="grade_id" class="form-select" required>
                        {% for grade in grades %}
                        <option value="{{ grade.id }}">{{ grade.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">اضافه کردن</button>
            </form>
            <table class="table mt-4">
                <thead>
                    <tr><th>نام کلاس</th><th>پایه</th><th>عملیات</th></tr>
                </thead>
                <tbody>
                    {% for cls in classes %}
                    <tr>
                        <td>{{ cls.name }}</td>
                        <td>{{ cls.grade.name }}</td>
                        <td>
                            <form method="POST" action="{{ url_for('admin.edit_class', class_id=cls.id) }}" class="d-inline">
                                <input type="text" name="name" value="{{ cls.name }}" class="form-control d-inline w-auto" style="width:80px;">
                                <select name="grade_id" class="form-select d-inline w-auto" style="width:100px;">
                                    {% for grade in grades %}
                                    <option value="{{ grade.id }}" {% if grade.id == cls.grade_id %}selected{% endif %}>{{ grade.name }}</option>
                                    {% endfor %}
                                </select>
                                <button type="submit" class="btn btn-sm btn-warning">ویرایش</button>
                            </form>
                            <a href="{{ url_for('admin.delete_class', class_id=cls.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('حذف شود؟')">حذف</a>
                            <button type="button" class="btn btn-sm btn-info" data-bs-toggle="modal" data-bs-target="#assignTeachers{{ cls.id }}">اختصاص معلم</button>
                            <button type="button" class="btn btn-sm btn-success" data-bs-toggle="modal" data-bs-target="#assignStudents{{ cls.id }}">اختصاص دانش‌آموز</button>
                        </td>
                    </tr>
                    <div class="modal fade" id="assignTeachers{{ cls.id }}" tabindex="-1">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5>اختصاص معلم به {{ cls.name }}</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <form method="POST" action="{{ url_for('admin.assign_teachers_to_class', class_id=cls.id) }}">
                                    <div class="modal-body">
                                        <select name="teacher_ids" class="form-select" multiple>
                                            {% for teacher in teachers %}
                                            <option value="{{ teacher.id }}" {% if teacher in cls.class_teachers %}selected{% endif %}>{{ teacher.first_name }} {{ teacher.last_name }}</option>
                                            {% endfor %}
                                        </select>
                                        <small>چند انتخاب با Ctrl+کلیک</small>
                                    </div>
                                    <div class="modal-footer">
                                        <button type="submit" class="btn btn-primary">ذخیره</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                    <div class="modal fade" id="assignStudents{{ cls.id }}" tabindex="-1">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5>اختصاص دانش‌آموز به {{ cls.name }} (از پایه {{ cls.grade.name }})</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <form method="POST" action="{{ url_for('admin.assign_students_to_class', class_id=cls.id) }}">
                                    <div class="modal-body">
                                        <select name="student_ids" class="form-select" multiple>
                                            {% for student in students if student.grade_id == cls.grade_id %}
                                            <option value="{{ student.id }}" {% if student.class_id == cls.id %}selected{% endif %}>{{ student.student_id }} - {{ student.first_name }} {{ student.last_name }}</option>
                                            {% endfor %}
                                        </select>
                                        <small>انتخاب از دانش‌آموزان پایه {{ cls.grade.name }}؛ چند انتخاب با Ctrl+کلیک</small>
                                    </div>
                                    <div class="modal-footer">
                                        <button type="submit" class="btn btn-primary">ذخیره</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </tbody>
            </table>
            {% endblock %}'''),
        'manage_teachers.html': textwrap.dedent('''\
            {% extends "base.html" %}
            {% block content %}
            <h2>مدیریت معلمان</h2>
            <form method="POST" action="{{ url_for('admin.add_teacher') }}">
                <div class="card mb-4">
                    <div class="card-header"><h5>اضافه کردن معلم</h5></div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label>نام کاربری</label>
                            <input type="text" name="username" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label>رمز عبور</label>
                            <input type="password" name="password" class="form-control" required>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <label>نام</label>
                                <input type="text" name="first_name" class="form-control" required>
                            </div>
                            <div class="col-md-6">
                                <label>نام خانوادگی</label>
                                <input type="text" name="last_name" class="form-control" required>
                            </div>
                        </div>
                        <div class="mb-3 mt-3">
                            <label>کلاس‌های تعلق (چند انتخاب)</label>
                            <select name="class_ids" class="form-select" multiple>
                                {% for cls in classes %}
                                <option value="{{ cls.id }}">{{ cls.name }}</option>
                                {% endfor %}
                            </select>
                            <small>چند کلاس با Ctrl+کلیک</small>
                        </div>
                        <button type="submit" class="btn btn-primary">اضافه کردن</button>
                    </div>
                </div>
            </form>
            <table class="table">
                <thead>
                    <tr><th>نام کاربری</th><th>نام کامل</th><th>کلاس‌ها</th><th>عملیات</th></tr>
                </thead>
                <tbody>
                    {% for teacher in teachers %}
                    <tr>
                        <td>{{ teacher.username }}</td>
                        <td>{{ teacher.first_name }} {{ teacher.last_name }}</td>
                        <td>{% for tc in teacher.teacher_classes %}{{ tc.class_.name }}{% if not loop.last %}, {% endif %}{% endfor %}</td>
                        <td>
                            <a href="{{ url_for('admin.edit_teacher', teacher_id=teacher.id) }}" class="btn btn-sm btn-warning">ویرایش</a>
                            <a href="{{ url_for('admin.delete_teacher', teacher_id=teacher.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('حذف شود؟')">حذف</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endblock %}'''),
        'edit_teacher.html': textwrap.dedent('''\
            {% extends "base.html" %}
            {% block content %}
            <h2>ویرایش معلم</h2>
            <form method="POST">
                <div class="mb-3">
                    <label>نام کاربری</label>
                    <input type="text" name="username" class="form-control" value="{{ teacher.username }}" required>
                </div>
                <div class="mb-3">
                    <label>رمز عبور جدید (خالی بگذارید برای بدون تغییر)</label>
                    <input type="password" name="password" class="form-control">
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <label>نام</label>
                        <input type="text" name="first_name" class="form-control" value="{{ teacher.first_name }}" required>
                    </div>
                    <div class="col-md-6">
                        <label>نام خانوادگی</label>
                        <input type="text" name="last_name" class="form-control" value="{{ teacher.last_name }}" required>
                    </div>
                </div>
                <div class="mb-3 mt-3">
                    <label>کلاس‌های تعلق (چند انتخاب)</label>
                    <select name="class_ids" class="form-select" multiple>
                        {% for cls in classes %}
                        <option value="{{ cls.id }}" {% if cls.id in teacher_class_ids %}selected{% endif %}>{{ cls.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">ذخیره</button>
                <a href="{{ url_for('admin.manage_teachers') }}" class="btn btn-secondary">انصراف</a>
            </form>
            {% endblock %}'''),
        'manage_students.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>مدیریت دانش آموزان</h2>
            <form method="POST" action="{{ url_for('admin.add_student') }}" class="mb-4">
                <div class="row">
                    <div class="col-md-2">
                        <input type="text" name="student_id" class="form-control" placeholder="کد دانش‌آموزی" required>
                    </div>
                    <div class="col-md-2">
                        <input type="text" name="first_name" class="form-control" placeholder="نام" required>
                    </div>
                    <div class="col-md-2">
                        <input type="text" name="last_name" class="form-control" placeholder="نام خانوادگی" required>
                    </div>
                    <div class="col-md-2">
                        <select name="grade_id" class="form-select" required>
                            {% for grade in grades %}
                            <option value="{{ grade.id }}">{{ grade.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-2">
                        <input type="text" name="parent_phone" class="form-control" placeholder="شماره والدین (0912...)">
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary">اضافه</button>
                    </div>
                </div>
            </form>
            <h4>وارد کردن از فایل CSV</h4>
            <form method="POST" action="{{ url_for('admin.import_students') }}" enctype="multipart/form-data">
                <div class="mb-3">
                    <input type="file" name="csv_file" class="form-control" accept=".csv" required>
                    <small>فرمت: student_id,first_name,last_name,grade_id,parent_phone</small>
                </div>
                <button type="submit" class="btn btn-success">وارد کردن</button>
            </form>
            <table class="table mt-4">
                <thead>
                    <tr><th>کد</th><th>نام</th><th>نام خانوادگی</th><th>پایه</th><th>کلاس</th><th>شماره والدین</th><th>عملیات</th></tr>
                </thead>
                <tbody>
                    {% for student in students %}
                    <tr>
                        <td>{{ student.student_id }}</td>
                        <td>{{ student.first_name }}</td>
                        <td>{{ student.last_name }}</td>
                        <td>{{ student.grade.name if student.grade else '' }}</td>
                        <td>{{ student.class_.name if student.class_ else 'بدون کلاس' }}</td>
                        <td>{{ student.parent_phone or 'عدم ثبت' }}</td>
                        <td>
                            <a href="{{ url_for('admin.edit_student', student_id=student.id) }}" class="btn btn-sm btn-warning">ویرایش</a>
                            <a href="{{ url_for('admin.delete_student', student_id=student.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('حذف شود؟')">حذف</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endblock %}''',
        'edit_student.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>ویرایش دانش‌آموز</h2>
            <form method="POST">
                <div class="mb-3">
                    <label>کد دانش‌آموزی</label>
                    <input type="text" name="student_id" class="form-control" value="{{ student.student_id }}" required>
                </div>
                <div class="mb-3">
                    <label>نام</label>
                    <input type="text" name="first_name" class="form-control" value="{{ student.first_name }}" required>
                </div>
                <div class="mb-3">
                    <label>نام خانوادگی</label>
                    <input type="text" name="last_name" class="form-control" value="{{ student.last_name }}" required>
                </div>
                <div class="mb-3">
                    <label>پایه</label>
                    <select name="grade_id" class="form-select" required>
                        {% for grade in grades %}
                        <option value="{{ grade.id }}" {% if student.grade_id == grade.id %}selected{% endif %}>{{ grade.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="mb-3">
                    <label>شماره والدین</label>
                    <input type="text" name="parent_phone" class="form-control" value="{{ student.parent_phone or '' }}" placeholder="09123456789">
                </div>
                <button type="submit" class="btn btn-primary">ذخیره</button>
                <a href="{{ url_for('admin.manage_students') }}" class="btn btn-secondary">انصراف</a>
            </form>
            {% endblock %}''',
        'manage_subjects.html': textwrap.dedent('''\
            {% extends "base.html" %}
            {% block content %}
            <h2>مدیریت دروس</h2>
            <form method="POST" action="{{ url_for('admin.add_subject') }}">
                <div class="mb-3">
                    <label>نام درس</label>
                    <input type="text" name="name" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label>کلاس</label>
                    <select name="class_id" class="form-select" required>
                        {% for cls in classes %}
                        <option value="{{ cls.id }}">{{ cls.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="mb-3">
                    <label>معلم</label>
                    <select name="teacher_id" class="form-select" required>
                        {% for teacher in teachers %}
                        <option value="{{ teacher.id }}">{{ teacher.first_name }} {{ teacher.last_name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">اضافه کردن</button>
            </form>
            <table class="table mt-4">
                <thead>
                    <tr><th>نام درس</th><th>کلاس</th><th>معلم</th><th>عملیات</th></tr>
                </thead>
                <tbody>
                    {% for subject in subjects %}
                    <tr>
                        <td>{{ subject.name }}</td>
                        <td>{{ subject.class_.name }}</td>
                        <td>{{ subject.teacher.first_name }} {{ subject.teacher.last_name }}</td>
                        <td>
                            <form method="POST" action="{{ url_for('admin.edit_subject', subject_id=subject.id) }}" class="d-inline">
                                <input type="text" name="name" value="{{ subject.name }}" class="form-control d-inline w-auto" style="width:80px;">
                                <select name="class_id" class="form-select d-inline w-auto" style="width:100px;">
                                    {% for cls in classes %}
                                    <option value="{{ cls.id }}" {% if subject.class_id == cls.id %}selected{% endif %}>{{ cls.name }}</option>
                                    {% endfor %}
                                </select>
                                <select name="teacher_id" class="form-select d-inline w-auto" style="width:120px;">
                                    {% for t in teachers %}
                                    <option value="{{ t.id }}" {% if subject.teacher_id == t.id %}selected{% endif %}>{{ t.first_name }} {{ t.last_name }}</option>
                                    {% endfor %}
                                </select>
                                <button type="submit" class="btn btn-sm btn-warning">ویرایش</button>
                            </form>
                            <a href="{{ url_for('admin.delete_subject', subject_id=subject.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('حذف شود؟')">حذف</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endblock %}'''),
        'teacher_dashboard.html': textwrap.dedent('''\
            {% extends "base.html" %}
            {% block content %}
            <h2>داشبورد معلم: {{ teacher.first_name }} {{ teacher.last_name }}</h2>
            <div class="row">
                {% for cls in classes %}
                <div class="col-md-6 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5>{{ cls.name }}</h5>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                {% for subject in subjects_by_class[cls.name] %}
                                <li>{{ subject.name }} <a href="{{ url_for('teacher.manage_scores', subject_id=subject.id) }}" class="btn btn-sm btn-outline-primary">نمره</a></li>
                                {% endfor %}
                            </ul>
                            <a href="{{ url_for('teacher.manage_attendance', class_id=cls.id) }}" class="btn btn-info me-2">حضورغیاب</a>
                            <a href="{{ url_for('teacher.manage_discipline', class_id=cls.id) }}" class="btn btn-warning me-2">بی‌انضباطی</a>
                            <a href="{{ url_for('teacher.manage_skills') }}" class="btn btn-success">مهارت‌ها</a>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endblock %}'''),
        'manage_scores.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>نمرات {{ subject.name }} (روز جاری: {{ jtoday }})</h2>
            <form method="GET" class="mb-3">
                <div class="row">
                    <div class="col-md-3">
                        <input type="text" name="from_date" class="form-control" placeholder="از تاریخ (شمسی YYYY/MM/DD)" value="{{ from_date_str or '' }}">
                    </div>
                    <div class="col-md-3">
                        <input type="text" name="to_date" class="form-control" placeholder="تا تاریخ (شمسی YYYY/MM/DD)" value="{{ to_date_str or '' }}">
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary">فیلتر</button>
                    </div>
                    <div class="col-md-2">
                        <a href="{{ url_for('teacher.manage_scores', subject_id=subject.id) }}" class="btn btn-secondary">امروز</a>  <!-- reset to today -->
                    </div>
                </div>
            </form>
            <form method="POST" action="{{ url_for('teacher.add_score') }}" class="mb-4">
                <div class="row">
                    <div class="col-md-3">
                        <select name="student_id" class="form-select" required>
                            {% for student in students %}
                            <option value="{{ student.id }}">{{ student.first_name }} {{ student.last_name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-2">
                        <input type="hidden" name="subject_id" value="{{ subject.id }}">
                        <input type="number" name="score" class="form-control" placeholder="نمره" step="0.25" min="0" max="20" required>
                    </div>
                    <div class="col-md-2">
                        <input type="text" name="date" class="form-control" placeholder="تاریخ شمسی YYYY/MM/DD" value="{{ jtoday }}" required>  <!-- default jtoday -->
                    </div>
                    <div class="col-md-3">
                        <select name="weekday" class="form-select" required>
                            <option value="">روز هفته را انتخاب کنید</option>
                            <option value="شنبه">شنبه</option>
                            <option value="یکشنبه">یکشنبه</option>
                            <option value="دوشنبه">دوشنبه</option>
                            <option value="سه‌شنبه">سه‌شنبه</option>
                            <option value="چهارشنبه">چهارشنبه</option>
                            <option value="پنجشنبه">پنجشنبه</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary w-100">ثبت نمره</button>
                    </div>
                </div>
            </form>
            <table class="table table-striped">
                <thead class="table-dark">
                    <tr><th>دانش‌آموز</th><th>نمره</th><th>تاریخ (شمسی)</th><th>روز</th><th>عملیات</th></tr>
                </thead>
                <tbody>
                    {% for sc in scores %}
                    <tr>
                        <td>{{ sc.student.first_name }} {{ sc.student.last_name }}</td>
                        <td>{{ sc.score }}</td>
                        <td>{{ sc.jdate }}</td>
                        <td>{{ sc.weekday }}</td>
                        <td>
                            <form method="POST" action="{{ url_for('teacher.edit_score', score_id=sc.id) }}" class="d-inline">
                                <input type="number" name="score" value="{{ sc.score }}" class="form-control d-inline w-auto" style="width:60px;" min="0" max="20">
                                <input type="text" name="date" value="{{ sc.jdate }}" class="form-control d-inline w-auto" style="width:100px;">
                                <select name="weekday" class="form-select d-inline w-auto" style="width:80px;">
                                    <option value="شنبه" {% if sc.weekday == 'شنبه' %}selected{% endif %}>شنبه</option>
                                    <option value="یکشنبه" {% if sc.weekday == 'یکشنبه' %}selected{% endif %}>یکشنبه</option>
                                    <option value="دوشنبه" {% if sc.weekday == 'دوشنبه' %}selected{% endif %}>دوشنبه</option>
                                    <option value="سه‌شنبه" {% if sc.weekday == 'سه‌شنبه' %}selected{% endif %}>سه‌شنبه</option>
                                    <option value="چهارشنبه" {% if sc.weekday == 'چهارشنبه' %}selected{% endif %}>چهارشنبه</option>
                                    <option value="پنجشنبه" {% if sc.weekday == 'پنجشنبه' %}selected{% endif %}>پنجشنبه</option>
                                </select>
                                <button type="submit" class="btn btn-sm btn-warning">ویرایش</button>
                            </form>
                            <a href="{{ url_for('teacher.delete_score', score_id=sc.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('حذف شود؟')">حذف</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="5" class="text-center text-muted">هیچ نمره‌ای یافت نشد.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
            {% if pagination %}
            {{ pagination.links }}
            {% endif %}
            {% endblock %}
            {% block scripts %}
            <script>
                const dateInput = document.querySelector('input[name="date"]');
                if (dateInput) {
                    dateInput.addEventListener('input', function() {
                        const value = this.value;
                        if (!/^\\\\d{4}\\\\d{2}\\\\d{2}$/.test(value)) {
                            this.setCustomValidity('فرمت: YYYY/MM/DD');
                        } else {
                            this.setCustomValidity('');
                        }
                    });
                }
            </script>
            {% endblock %}''',
        'manage_attendance.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>حضورغياب - {{ cls.name }} (روز جاری: {{ jtoday }})</h2>
            <form method="GET" class="mb-3">
                <div class="row">
                    <div class="col-md-3">
                        <input type="text" name="from_date" class="form-control" placeholder="از تاريخ (شمسي YYYY/MM/DD)" value="{{ from_date_str or '' }}">
                    </div>
                    <div class="col-md-3">
                        <input type="text" name="to_date" class="form-control" placeholder="تا تاريخ (شمسي YYYY/MM/DD)" value="{{ to_date_str or '' }}">
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary">فيلتر</button>
                    </div>
                    <div class="col-md-2">
                        <a href="{{ url_for('teacher.manage_attendance', class_id=cls.id) }}" class="btn btn-secondary">امروز</a>
                    </div>
                </div>
            </form>
            <form method="POST" action="{{ url_for('teacher.update_attendance') }}">
                <table class="table">
                    <thead><tr><th>دانش آموز</th><th>وضعيت</th><th>تاريخ (شمسي)</th><th>عملیات</th></tr></thead>
                    <tbody>
                        {% for student in students %}
                        <tr>
                            <td>{{ student.first_name }} {{ student.last_name }}</td>
                            <td>
                                <select name="status" class="form-select d-inline w-auto" style="width:100px;">
                                    <option value="present" {% if att_dict.get(student.id, {}).get('status', '') == 'present' %}selected{% endif %}>حاضر</option>
                                    <option value="absent" {% if att_dict.get(student.id, {}).get('status', '') == 'absent' %}selected{% endif %}>غايب</option>
                                    <option value="late" {% if att_dict.get(student.id, {}).get('status', '') == 'late' %}selected{% endif %}>تاخير</option>
                                </select>
                            </td>
                            <td>
                                <input type="text" name="date" value="{{ jtoday if not from_date_str else from_date_str }}" class="form-control d-inline w-auto" style="width:120px;" placeholder="شمسي YYYY/MM/DD">
                            </td>
                            <td>
                                <input type="hidden" name="student_id" value="{{ student.id }}">
                                <input type="hidden" name="class_id" value="{{ cls.id }}">
                                <button type="submit" class="btn btn-sm btn-primary">به‌روزرساني</button>
                                {% if att_dict.get(student.id) %}
                                <a href="{{ url_for('teacher.delete_attendance', att_id=att_dict[student.id]['att_id']) }}" class="btn btn-sm btn-danger">حذف</a>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </form>
            {% if pagination %}
            {{ pagination.links }}
            {% endif %}
            {% endblock %}
            {% block scripts %}
            <script>
                const dateInput = document.querySelector('input[name="date"]');
                if (dateInput) {
                    dateInput.addEventListener('input', function() {
                        const value = this.value;
                        if (!/^\\\\d{4}\\\\d{2}\\\\d{2}$/.test(value)) {  # فیکس: escaped regex
                            this.setCustomValidity('فرمت: YYYY/MM/DD');
                        } else {
                            this.setCustomValidity('');
                        }
                    });
                }
            </script>
            {% endblock %}''',
       'manage_discipline.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>بی‌انضباطی - {{ cls.name }} (روز جاری: {{ jtoday }})</h2>
            <form method="GET" class="mb-3">
                <div class="row">
                    <div class="col-md-3">
                        <input type="text" name="from_date" class="form-control" placeholder="از تاریخ (شمسی YYYY/MM/DD)" value="{{ from_date_str or '' }}">
                    </div>
                    <div class="col-md-3">
                        <input type="text" name="to_date" class="form-control" placeholder="تا تاریخ (شمسی YYYY/MM/DD)" value="{{ to_date_str or '' }}">
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary">فیلتر</button>
                    </div>
                    <div class="col-md-2">
                        <a href="{{ url_for('teacher.manage_discipline', class_id=cls.id) }}" class="btn btn-secondary">امروز</a>  # reset to today
                    </div>
                </div>
            </form>
            <form method="POST" action="{{ url_for('teacher.add_discipline') }}" class="mb-4">
                <div class="row">
                    <div class="col-md-3">
                        <select name="student_id" class="form-select">
                            {% for student in students %}
                            <option value="{{ student.id }}">{{ student.first_name }} {{ student.last_name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <input type="hidden" name="class_id" value="{{ cls.id }}">
                        <select name="discipline_type" class="form-select">
                            {% for disc in disciplines %}
                            <option value="{{ disc }}">{{ disc }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-2">
                        <input type="number" name="score" class="form-control" placeholder="نمره (منفی)" step="0.25" required>
                    </div>
                    <div class="col-md-2">
                        <input type="text" name="date" value="{{ jtoday if not from_date_str else from_date_str }}" class="form-control" placeholder="شمسی YYYY/MM/DD" required>  # default jtoday
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary w-100">ثبت</button>
                    </div>
                </div>
            </form>
            <table class="table">
                <thead><tr><th>دانش‌آموز</th><th>نوع</th><th>نمره</th><th>تاریخ (شمسی)</th><th>عملیات</th></tr></thead>
                <tbody>
                    {% for disc in disc_scores %}
                    <tr>
                        <td>{{ disc.student.first_name }} {{ disc.student.last_name }}</td>
                        <td>{{ disc.discipline_type }}</td>
                        <td>{{ disc.score }}</td>
                        <td>{{ disc.jdate }}</td>
                        <td><a href="{{ url_for('teacher.delete_discipline', disc_id=disc.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('حذف شود؟')">حذف</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% if pagination %}
            {{ pagination.links }}
            {% endif %}
            {% endblock %}
            {% block scripts %}
            <script>
                const dateInput = document.querySelector('input[name="date"]');
                if (dateInput) {
                    dateInput.addEventListener('input', function() {
                        const value = this.value;
                        if (!/^\\\\d{4}\\\\d{2}\\\\d{2}$/.test(value)) {
                            this.setCustomValidity('فرمت: YYYY/MM/DD');
                        } else {
                            this.setCustomValidity('');
                        }
                    });
                }
            </script>
            {% endblock %}''',
        'manage_skills.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>نمرات مهارتی (کلاس‌های شما)</h2>
            <form method="GET" class="mb-3">
                <div class="row">
                    <div class="col-md-3">
                        <input type="text" name="from_date" class="form-control" placeholder="از تاریخ (شمسی YYYY/MM/DD)" value="{{ from_date_str or '' }}">
                    </div>
                    <div class="col-md-3">
                        <input type="text" name="to_date" class="form-control" placeholder="تا تاریخ (شمسی YYYY/MM/DD)" value="{{ to_date_str or '' }}">
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary">فیلتر</button>
                    </div>
                </div>
            </form>
            <form method="POST" action="{{ url_for('teacher.add_skill_score') }}" class="mb-4">
                <div class="row">
                    <div class="col-md-3">
                        <select name="student_id" class="form-select" required>
                            {% for class_name, class_students in students_by_class.items() %}
                            <optgroup label="{{ class_name }}">
                                {% for student in class_students %}
                                <option value="{{ student.id }}">{{ student.first_name }} {{ student.last_name }}</option>
                                {% endfor %}
                            </optgroup>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <select name="skill_name" class="form-select">
                            {% for skill in skills %}
                            <option value="{{ skill }}">{{ skill }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-2">
                        <input type="number" name="score" class="form-control" placeholder="نمره" step="0.25" required>
                    </div>
                    <div class="col-md-2">
                        <input type="text" name="date" class="form-control" placeholder="تاریخ شمسی YYYY/MM/DD" required>
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary w-100">ثبت</button>
                    </div>
                </div>
            </form>
            <table class="table">
                <thead><tr><th>دانش‌آموز</th><th>مهارت</th><th>نمره</th><th>تاریخ (شمسی)</th><th>عملیات</th></tr></thead>
                <tbody>
                    {% for sk in skill_scores %}
                    <tr>
                        <td>{{ sk.student.first_name }} {{ sk.student.last_name }}</td>
                        <td>{{ sk.skill_name }}</td>
                        <td>{{ sk.score }}</td>
                        <td>{{ sk.jdate }}</td>
                        <td><a href="{{ url_for('teacher.delete_skill_score', skill_id=sk.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('حذف شود؟')">حذف</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% if pagination %}
            {{ pagination.links }}
            {% endif %}
            {% endblock %}
            {% block scripts %}
            <script>
                const dateInput = document.querySelector('input[name="date"]');
                if (dateInput) {
                    dateInput.addEventListener('input', function() {
                        const value = this.value;
                        if (!/^\\\\d{4}\\\\d{2}\\\\d{2}$/.test(value)) {
                            this.setCustomValidity('فرمت: YYYY/MM/DD');
                        } else {
                            this.setCustomValidity('');
                        }
                    });
                }
            </script>
            {% endblock %}''',
      'admin_attendance.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>غایبان و تأخیری‌ها (روز جاری: {{ jtoday }})</h2>
            <form method="GET" class="mb-3">
                <div class="row">
                    <div class="col-md-3">
                        <input type="text" name="from_date" class="form-control" placeholder="از تاریخ (شمسی YYYY/MM/DD)" value="{{ from_date_str or '' }}">
                    </div>
                    <div class="col-md-3">
                        <input type="text" name="to_date" class="form-control" placeholder="تا تاریخ (شمسی YYYY/MM/DD)" value="{{ to_date_str or '' }}">
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary">فیلتر</button>
                    </div>
                    <div class="col-md-2">
                        <a href="{{ url_for('admin.admin_attendance') }}" class="btn btn-secondary">امروز</a>  # reset to today
                    </div>
                </div>
            </form>
            <table class="table">
                <thead><tr><th>کلاس</th><th>دانش‌آموز</th><th>وضعیت</th><th>تاریخ (شمسی)</th><th>معلم</th></tr></thead>
                <tbody>
                    {% for att in attendances %}
                    <tr>
                        <td>{{ att.class_.name if att.class_ else 'نامشخص' }}</td>
                        <td>{{ att.student.first_name }} {{ att.student.last_name if att.student else 'نامشخص' }}</td>
                        <td>{{ att.status }}</td>
                        <td>{{ att.jdate }}</td>
                        <td>{{ att.teacher.first_name }} {{ att.teacher.last_name if att.teacher else 'نامشخص' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% if pagination %}
            {{ pagination.links }}
            {% endif %}
            {% if attendances|length == 0 %}
            <p class="text-muted">هیچ غایب یا تأخیری یافت نشد.</p>
            {% endif %}
            {% endblock %}''',
        'admin_manage_scores.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>نمرات {{ subject.name }} (ادمین)</h2>
            <form method="POST" action="{{ url_for('admin.admin_add_score') }}" class="mb-4">
                <!-- فرم مشابه manage_scores.html -->
                <div class="row">
                    <div class="col-md-3">
                        <select name="student_id" class="form-select">
                            {% for student in students %}
                            <option value="{{ student.id }}">{{ student.first_name }} {{ student.last_name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-2">
                        <input type="hidden" name="subject_id" value="{{ subject.id }}">
                        <input type="number" name="score" class="form-control" placeholder="نمره" step="0.25" required>
                    </div>
                    <div class="col-md-2">
                        <input type="date" name="date" class="form-control" required>
                    </div>
                    <div class="col-md-3">
                        <select name="weekday" class="form-select">
                            <option value="شنبه">شنبه</option>
                            <option value="یکشنبه">یکشنبه</option>
                            <!-- بقیه -->
                        </select>
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary w-100">ثبت نمره</button>
                    </div>
                </div>
            </form>
            <table class="table">
                <thead><tr><th>دانش‌آموز</th><th>نمره</th><th>تاریخ</th><th>روز</th><th>عملیات</th></tr></thead>
                <tbody>
                    {% for sc in scores %}
                    <tr>
                        <td>{{ sc.student.first_name }} {{ sc.student.last_name }}</td>
                        <td>{{ sc.score }}</td>
                        <td>{{ sc.date }}</td>
                        <td>{{ sc.weekday }}</td>
                        <td>
                            <form method="POST" action="{{ url_for('admin.admin_edit_score', score_id=sc.id) }}" class="d-inline">
                                <!-- فرم ویرایش مشابه -->
                                <button type="submit" class="btn btn-sm btn-warning">ویرایش</button>
                            </form>
                            <a href="{{ url_for('admin.admin_delete_score', score_id=sc.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('حذف شود؟')">حذف</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endblock %}''',
        'admin_discipline.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>لیست بی‌انضباطی (تعداد: {{ disciplines|length }})</h2>
            {% if negative_count > 0 %}
            <div class="alert alert-danger">تعداد نکات منفی: {{ negative_count }}</div>
            {% endif %}
            <table class="table">
                <thead><tr><th>دانش‌آموز</th><th>نوع</th><th>نمره</th><th>تاریخ (شمسی)</th><th>معلم</th></tr></thead>
                <tbody>
                    {% for disc in disciplines %}
                    <tr>
                        <td>{{ disc.student.first_name }} {{ disc.student.last_name if disc.student else 'نامشخص' }}</td>
                        <td>{{ disc.discipline_type }}</td>
                        <td>{{ disc.score }}</td>
                        <td>{{ disc.jdate }}</td>  <!-- فیکس: استفاده از jdate پاس‌شده -->
                        <td>{{ disc.teacher.first_name }} {{ disc.teacher.last_name if disc.teacher else 'نامشخص' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% if disciplines|length == 0 %}
            <p class="text-muted">هیچ بی‌انضباطی ثبت نشده. از داشبورد معلم ثبت کنید.</p>
            {% endif %}
            {% endblock %}''',
        'admin_reports.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>گزارش‌ها</h2>
            <form method="POST" action="{{ url_for('admin.generate_report') }}">
                <div class="row mb-2">
                    <div class="col-md-3">
                        <select name="report_type" class="form-select" required>
                            <option value="individual">فردی</option>
                            <option value="class">کلاس</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <select name="student_id" class="form-select d-none individual" required>
                            {% for student in students %}
                            <option value="{{ student.id }}">{{ student.first_name }} {{ student.last_name }}</option>
                            {% endfor %}
                        </select>
                        <select name="class_id" class="form-select d-none class" required>
                            {% for cls in classes %}
                            <option value="{{ cls.id }}">{{ cls.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-2">
                        <input type="text" name="from_date" class="form-control" placeholder="از تاریخ (شمسی YYYY/MM/DD)">
                    </div>
                    <div class="col-md-2">
                        <input type="text" name="to_date" class="form-control" placeholder="تا تاریخ (شمسی YYYY/MM/DD)">
                    </div>
                    <div class="col-md-2">
                        <select name="period_type" class="form-select">
                            <option value="daily">روزانه</option>
                            <option value="monthly">ماهانه</option>
                            <option value="quarterly">فصلی</option>
                        </select>
                    </div>
                </div>
                <div class="row mb-2">
                    <div class="col-md-3">
                        <select name="report_option" class="form-select">
                            <option value="average">میانگین نمرات</option>
                            <option value="total">جمع نمرات</option>
                            <option value="most_frequent">پرتکرارترین نمره</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-check-label"><input type="checkbox" name="include_skills" class="form-check-input"> شامل مهارت‌ها</label>
                    </div>
                    <div class="col-md-3">
                        <select name="format" class="form-select">
                            <option value="html">چارت + جدول</option>
                            <option value="excel">Excel</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <button type="submit" class="btn btn-primary">تولید گزارش</button>
                    </div>
                </div>
            </form>
            <script>
                document.querySelector('[name="report_type"]').addEventListener('change', function() {
                    document.querySelector('.individual').classList.toggle('d-none', this.value !== 'individual');
                    document.querySelector('.class').classList.toggle('d-none', this.value !== 'class');
                });
            </script>
            {% endblock %}''',
        'reports.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>گزارش‌ها</h2>
            <form method="POST" action="{{ url_for('admin.generate_report') }}">
                <div class="row mb-3">
                    <div class="col-md-3">
                        <select name="report_type" class="form-select" required>
                            <option value="individual">فردی</option>
                            <option value="class">کلاس</option>
                            <option value="transcript">کارنامه</option>
                        </select>
                    </div>
                    <div class="col-md-3 individual transcript">
                        <select name="student_id" class="form-select">
                            {% for student in students %}
                            <option value="{{ student.id }}">{{ student.first_name }} {{ student.last_name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-3 class">
                        <select name="class_id" class="form-select">
                            {% for cls in classes %}
                            <option value="{{ cls.id }}">{{ cls.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <input type="text" name="period" class="form-control" placeholder="دوره (اختیاری)">
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-md-3">
                        <input type="text" name="from_date" class="form-control" placeholder="از تاریخ (شمسی YYYY/MM/DD)">
                    </div>
                    <div class="col-md-3">
                        <input type="text" name="to_date" class="form-control" placeholder="تا تاریخ (شمسی YYYY/MM/DD)">
                    </div>
                    <div class="col-md-3">
                        <select name="period_type" class="form-select">
                            <option value="daily">روزانه</option>
                            <option value="monthly">ماهانه</option>
                            <option value="quarterly">فصلی</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-check-label"><input type="checkbox" name="include_skills" class="form-check-input"> شامل مهارت‌ها</label>
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-md-3">
                        <select name="report_option" class="form-select">
                            <option value="average">میانگین نمرات</option>
                            <option value="total">جمع نمرات</option>
                            <option value="most_frequent">پرتکرارترین نمره</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <select name="format" class="form-select">
                            <option value="html">چارت + جدول (نمایش + دانلود)</option>
                            <option value="excel">Excel (دانلود)</option>
                        </select>
                    </div>
                    <div class="col-md-6">
                        <button type="submit" class="btn btn-primary">تولید گزارش</button>
                    </div>
                </div>
            </form>
            <script>
                document.querySelector('[name="report_type"]').addEventListener('change', function() {
                    document.querySelector('.individual').classList.toggle('d-none', this.value !== 'individual');
                    document.querySelector('.class').classList.toggle('d-none', this.value !== 'class');
                    document.querySelector('.transcript').classList.toggle('d-none', this.value !== 'transcript');
                });
            </script>
            {% endblock %}''',
       'transcript_report.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>کارنامه {{ student.first_name }} {{ student.last_name }} ({{ from_date_str }} تا {{ to_date_str }})</h2>
            <a href="{{ url_for('admin.generate_report', report_type='transcript', student_id=student.id, from_date=from_date_str, to_date=to_date_str, format='excel') }}" class="btn btn-primary mb-3">دانلود Excel</a>
            <table class="table">
                <thead><tr><th>درس</th><th>نمره</th><th>تاریخ (شمسی)</th></tr></thead>
                <tbody>
                    {% for score in scores %}
                    <tr>
                        <td>{{ score.subject_ref.name }}</td>
                        <td>{{ score.score }}</td>
                        <td>{{ jdatetime.date.fromgregorian(date=score.date).strftime('%Y/%m/%d') }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% if skills %}
            <h3>مهارت‌ها</h3>
            <table class="table">
                <thead><tr><th>مهارت</th><th>نمره</th><th>تاریخ (شمسی)</th></tr></thead>
                <tbody>
                    {% for skill in skills %}
                    <tr>
                        <td>{{ skill.skill_name }}</td>
                        <td>{{ skill.score }}</td>
                        <td>{{ jdatetime.date.fromgregorian(date=skill.date).strftime('%Y/%m/%d') }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
            {% endblock %}''',
        
        'class_transcript_report.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>کارنامه کلاس {{ class_obj.name }} ({{ from_date_str }} تا {{ to_date_str }})</h2>
            <a href="{{ url_for('admin.generate_report', report_type='transcript', class_id=class_obj.id, from_date=from_date_str, to_date=to_date_str, format='excel') }}" class="btn btn-primary mb-3">دانلود Excel</a>
            <table class="table">
                <thead><tr><th>کد دانش‌آموزی</th><th>نام</th><th>نام خانوادگی</th><th>درس</th><th>نمره</th><th>تاریخ (شمسی)</th></tr></thead>
                <tbody>
                    {% for score in all_scores %}
                    <tr>
                        <td>{{ score.student.student_id }}</td>
                        <td>{{ score.student.first_name }}</td>
                        <td>{{ score.student.last_name }}</td>
                        <td>{{ score.subject_ref.name }}</td>
                        <td>{{ score.score }}</td>
                        <td>{{ jdatetime.date.fromgregorian(date=score.date).strftime('%Y/%m/%d') }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endblock %}''',
        'individual_report.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>گزارش فردی {{ student.first_name }} {{ student.last_name }} ({{ from_date_str }} تا {{ to_date_str }})</h2>
            <a href="{{ url_for('admin.generate_report', report_type='individual', student_id=student.id, from_date=from_date_str, to_date=to_date_str, format='excel') }}" class="btn btn-primary mb-3">دانلود Excel</a>
            <div class="row">
                <div class="col-md-6">
                    <canvas id="chart" width="400" height="200"></canvas>
                </div>
                <div class="col-md-6">
                    <table class="table">
                        <thead><tr><th>درس</th><th>نمره</th><th>تاریخ (شمسی)</th></tr></thead>
                        <tbody>
                            {% for score in scores %}
                            <tr>
                                <td>{{ score.subject_ref.name }}</td>
                                <td>{{ score.score }}</td>
                                <td>{{ score.jdate }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            <script>
                const ctx = document.getElementById('chart').getContext('2d');
                const labels = {{ scores | map(attribute='jdate') | list | tojson }};
                const data = {{ scores | map(attribute='score') | list | tojson }};
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'نمرات',
                            data: data,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderWidth: 2,
                            fill: false
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            </script>
            {% endblock %}''',
        
        'class_report.html': '''\
            {% extends "base.html" %}
            {% block content %}
            <h2>گزارش کلاس {{ class_obj.name }} ({{ from_date_str }} تا {{ to_date_str }})</h2>
            <a href="{{ url_for('admin.generate_report', report_type='class', class_id=class_obj.id, from_date=from_date_str, to_date=to_date_str, format='excel') }}" class="btn btn-primary mb-3">دانلود Excel</a>
            <div class="row">
                <div class="col-md-6">
                    <canvas id="chart" width="400" height="200"></canvas>
                </div>
                <div class="col-md-6">
                    <table class="table">
                        <thead><tr><th>دانش‌آموز</th><th>میانگین نمره</th></tr></thead>
                        <tbody>
                            {% for student in students %}
                            <tr>
                                <td>{{ student.first_name }} {{ student.last_name }}</td>
                                <td>{{ (student.scores | map(attribute='score') | sum / (student.scores | length) if student.scores else 0) | round(2) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            <script>
                const ctx = document.getElementById('chart').getContext('2d');
                const labels = {{ students | map(attribute='first_name') | list | tojson }};
                const data = [{% for student in students %}
                    {{ (student.scores | map(attribute='score') | sum / (student.scores | length) if student.scores else 0) | round(2) }}{% if not loop.last %}, {% endif %}
                {% endfor %}];
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'میانگین نمرات',
                            data: data,
                            backgroundColor: 'rgba(153, 102, 255, 0.2)',
                            borderColor: 'rgba(153, 102, 255, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            </script>
            {% endblock %}''',
    }
           
    for filename, content in templates.items():
        file_path = os.path.join(templates_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"تمپلیت ایجاد/بازنویسی شد: {filename}")





