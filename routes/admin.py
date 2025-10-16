from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session  # session اضافه
from models import db, Admin, Teacher, Grade, Class, Student, Subject, Attendance, DisciplineScore, Score, SkillScore, TeacherClass  # TeacherClass اضافه
from routes.general import login_required
from utils import generate_excel_report, generate_class_excel_report
from werkzeug.security import generate_password_hash
from datetime import date
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import func, desc
import jdatetime  # برای شمسی
from collections import Counter  # برای most_frequent
from flask_paginate import Pagination, get_page_args


admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required(role='admin')
def admin_dashboard():
    try:
        students_count = Student.query.count()
        teachers_count = Teacher.query.count()
        classes_count = Class.query.count()
        admin = Admin.query.first()
    except Exception as e:
        flash(f'خطا در بارگیری داشبورد: {str(e)}', 'error')
        students_count = teachers_count = classes_count = 0
        admin = Admin(school_name='مدرسه', principal_name='مدیر')  # default safe
    
    return render_template('admin_dashboard.html',
                           students_count=students_count,
                           teachers_count=teachers_count,
                           classes_count=classes_count,
                           admin=admin)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_settings():
    admin = Admin.query.first()
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        school_name = request.form.get('school_name')
        principal_name = request.form.get('principal_name')
       
        # بروزرسانی مدرسه/مدیر
        admin.school_name = school_name
        admin.principal_name = principal_name
       
        # تغییر username
        if new_username and new_username != admin.username:
            if Admin.query.filter_by(username=new_username).first():
                flash('نام کاربری تکراری است', 'error')
                return render_template('admin_settings.html', admin=admin)
            admin.username = new_username
            session['username'] = new_username  # بروزرسانی session
       
        # تغییر password
        if new_password:
            if len(new_password) < 6:
                flash('رمز عبور حداقل 6 کاراکتر باشد', 'error')
                return render_template('admin_settings.html', admin=admin)
            if new_password != confirm_password:
                flash('رمز عبور و تأیید مطابقت ندارد', 'error')
                return render_template('admin_settings.html', admin=admin)
            admin.password_hash = generate_password_hash(new_password)
            flash('رمز عبور تغییر یافت', 'success')
       
        try:
            db.session.commit()
            flash('تنظیمات با موفقیت ذخیره شد', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در ذخیره: {str(e)}', 'error')
    return render_template('admin_settings.html', admin=admin)

@admin_bp.route('/grades')
@login_required(role='admin')
def manage_grades():
    grades = Grade.query.all()
    return render_template('manage_grades.html', grades=grades)

@admin_bp.route('/grades/add', methods=['POST'])
@login_required(role='admin')
def add_grade():
    name = request.form.get('name')
    if name:
        try:
            grade = Grade(name=name)
            db.session.add(grade)
            db.session.commit()
            flash('پایه تحصیلی اضافه شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در اضافه: {str(e)}', 'error')
    return redirect(url_for('admin.manage_grades'))

@admin_bp.route('/grades/edit/<int:grade_id>', methods=['POST'])
@login_required(role='admin')
def edit_grade(grade_id):
    grade = Grade.query.get_or_404(grade_id)
    name = request.form.get('name')
    if name:
        try:
            grade.name = name
            db.session.commit()
            flash('پایه تحصیلی ویرایش شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در ویرایش: {str(e)}', 'error')
    return redirect(url_for('admin.manage_grades'))

@admin_bp.route('/grades/delete/<int:grade_id>')
@login_required(role='admin')
def delete_grade(grade_id):
    grade = Grade.query.get_or_404(grade_id)
    if grade.classes:
        flash('نمی‌توان پایه را حذف کرد؛ کلاس‌هایی وابسته وجود دارد', 'error')
    else:
        try:
            db.session.delete(grade)
            db.session.commit()
            flash('پایه تحصیلی حذف شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در حذف: {str(e)}', 'error')
    return redirect(url_for('admin.manage_grades'))

@admin_bp.route('/classes')
@login_required(role='admin')
def manage_classes():
    classes = Class.query.all()
    grades = Grade.query.all()
    teachers = Teacher.query.all()
    students = Student.query.all()
    return render_template('manage_classes.html', classes=classes, grades=grades, teachers=teachers, students=students)

@admin_bp.route('/classes/add', methods=['POST'])
@login_required(role='admin')
def add_class():
    name = request.form.get('name')
    grade_id = request.form.get('grade_id')
    if name and grade_id:
        try:
            class_obj = Class(name=name, grade_id=int(grade_id))
            db.session.add(class_obj)
            db.session.commit()
            flash('کلاس با موفقیت اضافه شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در اضافه: {str(e)}', 'error')
    return redirect(url_for('admin.manage_classes'))

@admin_bp.route('/classes/edit/<int:class_id>', methods=['POST'])
@login_required(role='admin')
def edit_class(class_id):
    cls = Class.query.get_or_404(class_id)
    name = request.form.get('name')
    grade_id = request.form.get('grade_id')
    if name and grade_id:
        try:
            cls.name = name
            cls.grade_id = int(grade_id)
            db.session.commit()
            flash('کلاس ویرایش شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در ویرایش: {str(e)}', 'error')
    return redirect(url_for('admin.manage_classes'))

@admin_bp.route('/classes/delete/<int:class_id>')
@login_required(role='admin')
def delete_class(class_id):
    cls = Class.query.get_or_404(class_id)
    if cls.students or cls.subjects:
        flash('نمی‌توان کلاس را حذف کرد؛ دانش‌آموز یا درس وابسته وجود دارد', 'error')
    else:
        try:
            db.session.delete(cls)
            db.session.commit()
            flash('کلاس حذف شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در حذف: {str(e)}', 'error')
    return redirect(url_for('admin.manage_classes'))

@admin_bp.route('/classes/assign_teachers/<int:class_id>', methods=['POST'])
@login_required(role='admin')
def assign_teachers_to_class(class_id):
    cls = Class.query.get_or_404(class_id)
    teacher_ids = request.form.getlist('teacher_ids')
    teacher_ids = list(set([tid for tid in teacher_ids if tid]))
    try:
        for tc in cls.class_teachers:
            db.session.delete(tc)
        for tid in teacher_ids:
            teacher = Teacher.query.get(int(tid))
            if teacher:
                tc = TeacherClass(teacher_id=int(tid), class_id=class_id)
                db.session.add(tc)
        db.session.commit()
        flash('معلمان با موفقیت اختصاص یافتند', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('خطا در اختصاص: تکراری یا نامعتبر', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('admin.manage_classes'))

@admin_bp.route('/classes/assign_students/<int:class_id>', methods=['POST'])
@login_required(role='admin')
def assign_students_to_class(class_id):
    cls = Class.query.get_or_404(class_id)
    student_ids = request.form.getlist('student_ids')
    grade_id = cls.grade_id
    try:
        for sid in student_ids:
            if sid:
                student = Student.query.get(int(sid))
                if student and student.grade_id == grade_id:
                    student.class_id = class_id
        db.session.commit()
        flash('دانش‌آموزان با موفقیت اختصاص یافتند', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('admin.manage_classes'))

@admin_bp.route('/teachers')
@login_required(role='admin')
def manage_teachers():
    teachers = Teacher.query.all()
    classes = Class.query.all()
    return render_template('manage_teachers.html', teachers=teachers, classes=classes)

@admin_bp.route('/teachers/add', methods=['POST'])
@login_required(role='admin')
def add_teacher():
    username = request.form.get('username')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    class_ids = request.form.getlist('class_ids')
    if username and password and first_name and last_name:
        try:
            teacher = Teacher(
                username=username,
                password_hash=generate_password_hash(password),
                first_name=first_name,
                last_name=last_name
            )
            db.session.add(teacher)
            db.session.flush()
            for cid in class_ids:
                if cid:
                    tc = TeacherClass(teacher_id=teacher.id, class_id=int(cid))
                    db.session.add(tc)
            db.session.commit()
            flash('معلم با موفقیت اضافه شد', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('نام کاربری تکراری است', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('admin.manage_teachers'))

@admin_bp.route('/teachers/edit/<int:teacher_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    classes = Class.query.all()
    if request.method == 'POST':
        try:
            teacher.first_name = request.form.get('first_name')
            teacher.last_name = request.form.get('last_name')
            teacher.username = request.form.get('username')
            new_password = request.form.get('password')
            if new_password:
                teacher.password_hash = generate_password_hash(new_password)
            class_ids = request.form.getlist('class_ids')
            for tc in teacher.teacher_classes:
                db.session.delete(tc)
            for cid in class_ids:
                if cid:
                    tc = TeacherClass(teacher_id=teacher_id, class_id=int(cid))
                    db.session.add(tc)
            db.session.commit()
            flash('معلم ویرایش شد', 'success')
            return redirect(url_for('admin.manage_teachers'))
        except IntegrityError:
            db.session.rollback()
            flash('نام کاربری تکراری است', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا: {str(e)}', 'error')
    return render_template('edit_teacher.html', teacher=teacher, classes=classes)

@admin_bp.route('/teachers/delete/<int:teacher_id>')
@login_required(role='admin')
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    if teacher.subjects:
        flash('نمی‌توان معلم را حذف کرد؛ درسی وابسته وجود دارد', 'error')
    else:
        try:
            db.session.delete(teacher)
            db.session.commit()
            flash('معلم حذف شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('admin.manage_teachers'))

@admin_bp.route('/students')
@login_required(role='admin')
def manage_students():
    students = Student.query.all()
    grades = Grade.query.all()
    return render_template('manage_students.html', students=students, grades=grades)

@admin_bp.route('/students/add', methods=['POST'])
@login_required(role='admin')
def add_student():
    student_id = request.form.get('student_id')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    grade_id = request.form.get('grade_id')
    parent_phone = request.form.get('parent_phone') or None
    if all([student_id, first_name, last_name, grade_id]):
        if Student.query.filter_by(student_id=student_id).first():
            flash('کد دانش‌آموزی تکراری است', 'error')
            return redirect(url_for('admin.manage_students'))
        try:
            student = Student(
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                grade_id=int(grade_id),
                class_id=None,
                parent_phone=parent_phone
            )
            db.session.add(student)
            db.session.commit()
            flash('دانش آموز با موفقیت اضافه شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('admin.manage_students'))

@admin_bp.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    grades = Grade.query.all()
    if request.method == 'POST':
        try:
            student.student_id = request.form.get('student_id')
            student.first_name = request.form.get('first_name')
            student.last_name = request.form.get('last_name')
            student.grade_id = int(request.form.get('grade_id'))
            student.parent_phone = request.form.get('parent_phone') or None
            db.session.commit()
            flash('دانش‌آموز ویرایش شد', 'success')
            return redirect(url_for('admin.manage_students'))
        except Exception as e:
            db.session.rollback()
            flash(f'خطا: {str(e)}', 'error')
    return render_template('edit_student.html', student=student, grades=grades)

@admin_bp.route('/students/import', methods=['POST'])
@login_required(role='admin')
def import_students():
    if 'csv_file' not in request.files:
        flash('فایل CSV انتخاب نشده', 'error')
        return redirect(url_for('admin.manage_students'))
    file = request.files['csv_file']
    if file.filename == '':
        flash('فایل CSV انتخاب نشده', 'error')
        return redirect(url_for('admin.manage_students'))
    try:
        # فیکس: CSV با csv module (بدون pandas)
        import csv
        from io import StringIO
        stream = StringIO(file.stream.read().decode('utf-8'))
        csv_reader = csv.DictReader(stream)
        required_cols = ['student_id', 'first_name', 'last_name', 'grade_id']
        if not all(col in csv_reader.fieldnames for col in required_cols):
            flash('ستون‌های مورد نیاز: student_id,first_name,last_name,grade_id (parent_phone اختیاری)', 'error')
            return redirect(url_for('admin.manage_students'))
        success_count = 0
        for row in csv_reader:
            if Student.query.filter_by(student_id=row['student_id']).first():
                continue
            student = Student(
                student_id=str(row['student_id']),
                first_name=str(row['first_name']),
                last_name=str(row['last_name']),
                grade_id=int(row['grade_id']),
                class_id=None,
                parent_phone=str(row.get('parent_phone', '')) or None
            )
            db.session.add(student)
            success_count += 1
        db.session.commit()
        flash(f'{success_count} دانش‌آموز با موفقیت وارد شد', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطا در import: {str(e)}', 'error')
    return redirect(url_for('admin.manage_students'))

@admin_bp.route('/students/delete/<int:student_id>')
@login_required(role='admin')
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    if student.scores or student.skills:
        flash('نمی‌توان دانش‌آموز را حذف کرد؛ نمره‌ای ثبت شده', 'error')
    else:
        try:
            db.session.delete(student)
            db.session.commit()
            flash('دانش‌آموز حذف شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('admin.manage_students'))

@admin_bp.route('/subjects')
@login_required(role='admin')
def manage_subjects():
    subjects = Subject.query.all()
    classes = Class.query.all()
    teachers = Teacher.query.all()
    return render_template('manage_subjects.html', subjects=subjects, classes=classes, teachers=teachers)

@admin_bp.route('/subjects/add', methods=['POST'])
@login_required(role='admin')
def add_subject():
    name = request.form.get('name')
    class_id = request.form.get('class_id')
    teacher_id = request.form.get('teacher_id')
    if all([name, class_id, teacher_id]):
        try:
            subject = Subject(name=name, class_id=int(class_id), teacher_id=int(teacher_id))
            db.session.add(subject)
            db.session.commit()
            flash('درس با موفقیت اضافه شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('admin.manage_subjects'))

@admin_bp.route('/subjects/edit/<int:subject_id>', methods=['POST'])
@login_required(role='admin')
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    try:
        subject.name = request.form.get('name')
        subject.class_id = int(request.form.get('class_id'))
        subject.teacher_id = int(request.form.get('teacher_id'))
        db.session.commit()
        flash('درس ویرایش شد', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('admin.manage_subjects'))

@admin_bp.route('/subjects/delete/<int:subject_id>')
@login_required(role='admin')
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if subject.scores:
        flash('نمی‌توان درس را حذف کرد؛ نمره‌ای ثبت شده', 'error')
    else:
        try:
            db.session.delete(subject)
            db.session.commit()
            flash('درس حذف شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('admin.manage_subjects'))

@admin_bp.route('/discipline')
@login_required(role='admin')
def admin_discipline():
    disciplines = DisciplineScore.query.options(joinedload(DisciplineScore.student), joinedload(DisciplineScore.teacher)).all()
    negative_count = len([disc for disc in disciplines if disc.score < 0])
    
    # تبدیل شمسی
    for disc in disciplines:
        jdate = jdatetime.date.fromgregorian(date=disc.date).strftime('%Y/%m/%d')
        disc.jdate = jdate
    
    return render_template('admin_discipline.html', disciplines=disciplines, negative_count=negative_count)
@admin_bp.route('/attendance')
@login_required(role='admin')
def admin_attendance():
    try:
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        from_date = None
        to_date = None
        
        # فیکس: default today
        today = date.today()
        jtoday = jdatetime.date.fromgregorian(date=today).strftime('%Y/%m/%d')
        
        if from_date_str:
            j_from = jdatetime.datetime.strptime(from_date_str, '%Y/%m/%d').togregorian().date()
            from_date = j_from
        else:
            from_date = today  # default today
        
        if to_date_str:
            j_to = jdatetime.datetime.strptime(to_date_str, '%Y/%m/%d').togregorian().date()
            to_date = j_to
        else:
            to_date = today  # default today
        
        # فیکس: query فقط غایب/تأخیر + فیلتر date (default today)
        query = Attendance.query.filter(
            Attendance.status.in_(['absent', 'late']),
            Attendance.date >= from_date,
            Attendance.date <= to_date
        ).options(joinedload(Attendance.student), joinedload(Attendance.class_), joinedload(Attendance.teacher))
        
        # pagination
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = 38
        total = query.count()
        attendances = query.offset(offset).limit(per_page).all()
        
        # شمسی
        for att in attendances:
            jdate = jdatetime.date.fromgregorian(date=att.date).strftime('%Y/%m/%d')
            att.jdate = jdate
        
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        
        return render_template('admin_attendance.html', attendances=attendances, pagination=pagination, from_date_str=from_date_str or jtoday, to_date_str=to_date_str or jtoday, jtoday=jtoday)
    except Exception as e:
        flash(f'خطا در بارگیری: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    except Exception as e:
        flash(f'خطا در بارگذاری حضورغیاب: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))
def admin_discipline():
    disciplines = DisciplineScore.query.options(joinedload(DisciplineScore.student), joinedload(DisciplineScore.teacher)).all()
    negative_count = len([disc for disc in disciplines if disc.score < 0])
    # تبدیل شمسی
    for disc in disciplines:
        jdate = jdatetime.date.fromgregorian(date=disc.date).strftime('%Y/%m/%d')
        disc.jdate = jdate
    return render_template('admin_discipline.html', disciplines=disciplines, negative_count=negative_count)

@admin_bp.route('/reports')
@login_required(role='admin')
def reports():
    students = Student.query.all()
    classes = Class.query.all()
    return render_template('reports.html', students=students, classes=classes)

@admin_bp.route('/reports/generate', methods=['POST'])
@login_required(role='admin')
def generate_report():
    report_type = request.form.get('report_type')  # individual/class/transcript
    student_id = request.form.get('student_id') or None
    class_id = request.form.get('class_id') or None
    from_date_str = request.form.get('from_date') or None  # شمسی از
    to_date_str = request.form.get('to_date') or None  # شمسی تا
    period_type = request.form.get('period_type', 'daily')  # daily/monthly/quarterly
    report_option = request.form.get('report_option', 'average')  # average/total/most_frequent
    include_skills = request.form.get('include_skills') == 'on'
    format_type = request.form.get('format', 'html')  # html/excel/view

    # تبدیل شمسی به میلادی
    from_date = None
    to_date = None
    if from_date_str:
        try:
            j_from = jdatetime.datetime.strptime(from_date_str, '%Y/%m/%d').togregorian().date()
            from_date = j_from
        except:
            flash('تاریخ از نامعتبر', 'error')
            return redirect(url_for('admin.reports'))
    if to_date_str:
        try:
            j_to = jdatetime.datetime.strptime(to_date_str, '%Y/%m/%d').togregorian().date()
            to_date = j_to
        except:
            flash('تاریخ تا نامعتبر', 'error')
            return redirect(url_for('admin.reports'))

    try:
        if report_type == 'individual' and student_id:
            student = Student.query.options(joinedload(Student.scores)).get(student_id)
            base_query = Score.query.filter_by(student_id=student_id)
            if from_date:
                base_query = base_query.filter(Score.date >= from_date)
            if to_date:
                base_query = base_query.filter(Score.date <= to_date)
            scores = base_query.all()

            # فیلتر دوره
            if period_type == 'monthly':
                current_month = jdatetime.date.today().month
                scores = [s for s in scores if jdatetime.date.fromgregorian(date=s.date).month == current_month]
            elif period_type == 'quarterly':
                current_quarter = (jdatetime.date.today().month - 1) // 3 + 1
                scores = [s for s in scores if ((jdatetime.date.fromgregorian(date=s.date).month - 1) // 3 + 1) == current_quarter]

            # گزینه گزارش
            if report_option == 'total':
                report_data = sum(s.score for s in scores) if scores else 0
            elif report_option == 'most_frequent':
                counter = Counter(s.score for s in scores)
                report_data = counter.most_common(1)[0][0] if counter else 0
            else:  # average
                report_data = sum(s.score for s in scores) / len(scores) if scores else 0

            skills = SkillScore.query.filter_by(student_id=student_id).all() if include_skills else []

            if format_type == 'excel':
                return generate_excel_report(student, scores, skills, f"{from_date_str or ''} to {to_date_str or ''}")
            elif format_type == 'view':
                # فیکس: مشاهده در صفحه (جدول + چارت)
                scores_with_date = []
                for s in scores:
                    s.jdate = jdatetime.date.fromgregorian(date=s.date).strftime('%Y/%m/%d')
                    scores_with_date.append(s)
                skills_with_date = []
                for sk in skills:
                    sk.jdate = jdatetime.date.fromgregorian(date=sk.date).strftime('%Y/%m/%d')
                    skills_with_date.append(sk)
                return render_template('individual_report.html', student=student, scores=scores_with_date, skills=skills_with_date, report_type=report_type, report_data=report_data, period_type=period_type, from_date_str=from_date_str, to_date_str=to_date_str)
            else:  # chart
                # فیکس: safe tojson for chart data
                labels = [s.subject_ref.name if s.subject_ref else 'نامشخص' for s in scores]  # safe labels
                data = [s.score for s in scores]  # safe data
                return render_template('chart_report.html', student=student, scores=scores, report_type=report_type, report_data=report_data, period_type=period_type, from_date_str=from_date_str, to_date_str=to_date_str, labels=labels, data=data)

       
    except Exception as e:
        flash(f'خطا در گزارش: {str(e)}', 'error')
        return redirect(url_for('admin.reports'))
        
def generate_transcript_excel(student, scores, skills, period):
    output = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = f'کارنامه {student.first_name} {student.last_name}'
    ws.append(['درس', 'نمره', 'تاریخ (شمسی)'])
    for score in scores:
        jdate = jdatetime.date.fromgregorian(date=score.date).strftime('%Y/%m/%d')
        ws.append([score.subject_ref.name, score.score, jdate])
    if skills:
        ws_skills = wb.create_sheet('مهارت‌ها')
        ws_skills.append(['مهارت', 'نمره', 'تاریخ (شمسی)'])
        for skill in skills:
            jdate = jdatetime.date.fromgregorian(date=skill.date).strftime('%Y/%m/%d')
            ws_skills.append([skill.skill_name, skill.score, jdate])
    wb.save(output)
    output.seek(0)
    filename = f'transcript_{student.first_name}_{student.last_name}_{period}.xlsx'
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)

def generate_class_transcript_excel(class_obj, students, all_scores, period):
    output = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = f'کارنامه کلاس {class_obj.name}'
    ws.append(['کد دانش‌آموزی', 'نام', 'نام خانوادگی', 'درس', 'نمره', 'تاریخ (شمسی)'])
    for student in students:
        s_scores = [sc for sc in all_scores if sc.student_id == student.id]
        for sc in s_scores:
            jdate = jdatetime.date.fromgregorian(date=sc.date).strftime('%Y/%m/%d')
            ws.append([student.student_id, student.first_name, student.last_name, sc.subject_ref.name, sc.score, jdate])
    wb.save(output)
    output.seek(0)
    filename = f'class_transcript_{class_obj.name}_{period}.xlsx'
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)
