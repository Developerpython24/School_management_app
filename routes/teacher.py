from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, Teacher, Subject, Student, Score, SkillScore, Attendance, DisciplineScore, Class, TeacherClass,  Admin
from routes.general import login_required
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
import jdatetime
from kavenegar import KavenegarAPI  # برای SMS
from flask_paginate import Pagination, get_page_args


api_key = '5A56496148425477335667304857624E582F4F3453597739435656354B6F516E627434327A327A56336F633D'  # جایگزین با API key خودت
api = KavenegarAPI(api_key)

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/dashboard')
@login_required(role='teacher')
def teacher_dashboard():
    teacher = Teacher.query.get(session['user_id'])
    class_ids = [tc.class_id for tc in teacher.teacher_classes]
    classes = Class.query.filter(Class.id.in_(class_ids)).all()
    subjects_by_class = {}
    for cls in classes:
        subjects = Subject.query.filter_by(class_id=cls.id, teacher_id=teacher.id).all()
        subjects_by_class[cls.name] = subjects
    return render_template('teacher_dashboard.html', teacher=teacher, classes=classes, subjects_by_class=subjects_by_class)


@teacher_bp.route('/scores/<int:subject_id>')
@login_required(role='teacher')
def manage_scores(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if subject.teacher_id != session['user_id']:
        flash('شما دسترسی به این درس ندارید', 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    
    students = Student.query.filter_by(class_id=subject.class_id).all()
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')
    from_date = None
    to_date = None
    if from_date_str:
        j_from = jdatetime.datetime.strptime(from_date_str, '%Y/%m/%d').togregorian().date()
        from_date = j_from
    if to_date_str:
        j_to = jdatetime.datetime.strptime(to_date_str, '%Y/%m/%d').togregorian().date()
        to_date = j_to
    
    query = Score.query.filter_by(subject_id=subject_id).options(joinedload(Score.student))
    if from_date:
        query = query.filter(Score.date >= from_date)
    if to_date:
        query = query.filter(Score.date <= to_date)
    
    # pagination
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 20
    total = query.count()
    scores = query.offset(offset).limit(per_page).all()
    
    # شمسی
    for sc in scores:
        jdate = jdatetime.date.fromgregorian(date=sc.date).strftime('%Y/%m/%d')
        sc.jdate = jdate
    
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
    
    return render_template('manage_scores.html', subject=subject, students=students, scores=scores, pagination=pagination, from_date_str=from_date_str, to_date_str=to_date_str)
@teacher_bp.route('/scores/add', methods=['POST'])
@login_required(role='teacher')
def add_score():
    student_id = request.form.get('student_id')
    subject_id = request.form.get('subject_id')
    score = request.form.get('score')
    date_str = request.form.get('date')  # شمسی YYYY/MM/DD
    weekday = request.form.get('weekday')
    
    if all([student_id, subject_id, score, date_str, weekday]):
        try:
            # فیکس: parse شمسی YYYY/MM/DD
            date_parts = date_str.split('/')
            if len(date_parts) != 3 or not all(part.isdigit() for part in date_parts):
                raise ValueError("فرمت تاریخ نامعتبر. از YYYY/MM/DD استفاده کنید.")
            year, month, day = map(int, date_parts)
            jdate = jdatetime.date(year, month, day)
            gdate = jdate.togregorian()
            
            # چک معتبر بودن (اختیاری)
            if gdate < date(1900, 1, 1) or gdate > date.today():
                raise ValueError("تاریخ خارج از محدوده معتبر است.")
            
            score_obj = Score(
                student_id=int(student_id),
                subject_id=int(subject_id),
                score=float(score),
                date=gdate,  # میلادی ذخیره
                weekday=weekday
            )
            db.session.add(score_obj)
            db.session.commit()
            flash('نمره با موفقیت ثبت شد', 'success')
        except ValueError as ve:
            db.session.rollback()
            flash(f'خطا در تاریخ شمسی: {str(ve)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در ثبت نمره: {str(e)}', 'error')
    else:
        flash('لطفاً همه فیلدها را پر کنید', 'error')
    
    return redirect(url_for('teacher.manage_scores', subject_id=subject_id))

@teacher_bp.route('/scores/edit/<int:score_id>', methods=['POST'])
@login_required(role='teacher')
def edit_score(score_id):
    score = Score.query.get_or_404(score_id)
    if score.subject_ref.teacher_id != session['user_id']:
        flash('دسترسی ندارید', 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    
    try:
        score.score = float(request.form.get('score'))
        date_str = request.form.get('date')  # شمسی YYYY/MM/DD
        date_parts = date_str.split('/')
        if len(date_parts) != 3 or not all(part.isdigit() for part in date_parts):
            raise ValueError("فرمت تاریخ نامعتبر. از YYYY/MM/DD استفاده کنید.")
        year, month, day = map(int, date_parts)
        jdate = jdatetime.date(year, month, day)
        score.date = jdate.togregorian()
        score.weekday = request.form.get('weekday')
        db.session.commit()
        flash('نمره ویرایش شد', 'success')
    except ValueError as ve:
        db.session.rollback()
        flash(f'خطا در تاریخ شمسی: {str(ve)}', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('teacher.manage_scores', subject_id=score.subject_id))
@teacher_bp.route('/scores/delete/<int:score_id>')
@login_required(role='teacher')
def delete_score(score_id):
    score = Score.query.get_or_404(score_id)
    if score.subject_ref.teacher_id != session['user_id']:
        flash('دسترسی ندارید', 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    subject_id = score.subject_id
    try:
        db.session.delete(score)
        db.session.commit()
        flash('نمره حذف شد', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطا در حذف: {str(e)}', 'error')
    return redirect(url_for('teacher.manage_scores', subject_id=subject_id))

@teacher_bp.route('/skills')
@login_required(role='teacher')
def manage_skills():
    teacher = Teacher.query.get(session['user_id'])
    class_ids = [tc.class_id for tc in teacher.teacher_classes]
    students = Student.query.filter(Student.class_id.in_(class_ids)).all()
    
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')
    from_date = None
    to_date = None
    if from_date_str:
        j_from = jdatetime.datetime.strptime(from_date_str, '%Y/%m/%d').togregorian().date()
        from_date = j_from
    if to_date_str:
        j_to = jdatetime.datetime.strptime(to_date_str, '%Y/%m/%d').togregorian().date()
        to_date = j_to
    
    query = SkillScore.query.filter_by(teacher_id=teacher.id)
    if from_date:
        query = query.filter(SkillScore.date >= from_date)
    if to_date:
        query = query.filter(SkillScore.date <= to_date)
    
    # pagination
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 20
    total = query.count()
    skill_scores = query.offset(offset).limit(per_page).all()
    
    # شمسی
    for sk in skill_scores:
        jdate = jdatetime.date.fromgregorian(date=sk.date).strftime('%Y/%m/%d')
        sk.jdate = jdate
    
    skills = ['مهارت شنوایی', 'مهارت سخنرانی', 'مهارت نوشتاری', 'مهارت حل مسئله', 'مهارت تفکر نقاد', 'مهارت هنری']
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
    
    return render_template('manage_skills.html', students=students, skills=skills, skill_scores=skill_scores, pagination=pagination, from_date_str=from_date_str, to_date_str=to_date_str)
@teacher_bp.route('/skills/add', methods=['POST'])
@login_required(role='teacher')
def add_skill_score():
    student_id = request.form.get('student_id')
    skill_name = request.form.get('skill_name')
    score = request.form.get('score')
    date_str = request.form.get('date')  # شمسی YYYY/MM/DD
    if all([student_id, skill_name, score, date_str]):
        try:
            date_parts = date_str.split('/')
            jdate = jdatetime.date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
            gdate = jdate.togregorian()
            skill_score = SkillScore(
                student_id=int(student_id),
                skill_name=skill_name,
                score=float(score),
                date=gdate,
                teacher_id=session['user_id']
            )
            db.session.add(skill_score)
            db.session.commit()
            flash('نمره مهارت با موفقیت ثبت شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('teacher.manage_skills'))

@teacher_bp.route('/skills/delete/<int:skill_id>')
@login_required(role='teacher')
def delete_skill_score(skill_id):
    skill = SkillScore.query.get_or_404(skill_id)
    if skill.teacher_id != session['user_id']:
        flash('دسترسی ندارید', 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    try:
        db.session.delete(skill)
        db.session.commit()
        flash('نمره مهارت حذف شد', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('teacher.manage_skills'))

@teacher_bp.route('/attendance/<int:class_id>')
@login_required(role='teacher')
def manage_attendance(class_id):
    teacher = Teacher.query.get(session['user_id'])
    cls = Class.query.get_or_404(class_id)
    if not any(tc.class_id == class_id for tc in teacher.teacher_classes):
        flash('شما دسترسی به این کلاس ندارید', 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    students = Student.query.filter_by(class_id=class_id).all()
    today = date.today()
    jtoday = jdatetime.date.fromgregorian(date=today).strftime('%Y/%m/%d')
    attendances = Attendance.query.filter_by(class_id=class_id, date=today).all()
    att_dict = {}
    for att in attendances:
        att_dict[att.student_id] = {
            'status': att.status,
            'att_id': att.id
        }
    
    return render_template('manage_attendance.html', cls=cls, students=students, att_dict=att_dict, today=today, jtoday=jtoday)

@teacher_bp.route('/attendance/update', methods=['POST'])
@login_required(role='teacher')
def update_attendance():
    student_id = request.form.get('student_id')
    class_id = request.form.get('class_id')
    status = request.form.get('status')
    date_str = request.form.get('date')  # شمسی YYYY/MM/DD
    teacher_id = session['user_id']
    if all([student_id, class_id, status, date_str]):
        try:
            # parse شمسی
            date_parts = date_str.split('/')
            if len(date_parts) != 3 or not all(part.isdigit() for part in date_parts):
                raise ValueError("فرمت تاریخ نامعتبر. از YYYY/MM/DD استفاده کنید.")
            year, month, day = map(int, date_parts)
            jdate = jdatetime.date(year, month, day)
            gdate = jdate.togregorian()
            
            old_att = Attendance.query.filter_by(student_id=int(student_id), class_id=int(class_id), date=gdate).first()
            if old_att:
                db.session.delete(old_att)
            att = Attendance(
                student_id=int(student_id),
                class_id=int(class_id),
                status=status,
                date=gdate,
                teacher_id=teacher_id
            )
            db.session.add(att)
            db.session.commit()
            flash('حضورغیاب به‌روزرسانی شد', 'success')
            
            # فیکس: SMS برای غایب/تأخیر (با Admin import)
            if status in ['absent', 'late']:
                student = Student.query.get(int(student_id))
                if student and student.parent_phone:
                    school_name = Admin.query.first().school_name if Admin.query.first() else 'مدرسه'  # safe
                    jdate_str = jdate.strftime('%Y/%m/%d')
                    message = f"دانش‌آموز {student.first_name} {student.last_name} در {jdate_str} {status} داشت. {school_name}."
                    try:
                        response = api.sms_send(student.parent_phone, message)
                        print(f"SMS sent to {student.parent_phone}: {response}")
                        flash('SMS به والدین ارسال شد', 'success')
                    except Exception as sms_e:
                        print(f"SMS error: {sms_e}")
                        flash('خطا در ارسال SMS (چک کن API key)', 'warning')  # optional flash
        except ValueError as ve:
            db.session.rollback()
            flash(f'خطا در تاریخ شمسی: {str(ve)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('teacher.manage_attendance', class_id=class_id))


from flask_paginate import Pagination, get_page_args

@teacher_bp.route('/discipline/<int:class_id>')
@login_required(role='teacher')
def manage_discipline(class_id):
    teacher = Teacher.query.get(session['user_id'])
    cls = Class.query.get_or_404(class_id)
    if not any(tc.class_id == class_id for tc in teacher.teacher_classes):
        flash('شما دسترسی به این کلاس ندارید', 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    
    students = Student.query.filter_by(class_id=class_id).all()
    disciplines = ['تأخیر', 'عدم توجه', 'نقض مقررات', 'غیبت غیرموجه']
    
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')
    from_date = None
    to_date = None
    if from_date_str:
        j_from = jdatetime.datetime.strptime(from_date_str, '%Y/%m/%d').togregorian().date()
        from_date = j_from
    if to_date_str:
        j_to = jdatetime.datetime.strptime(to_date_str, '%Y/%m/%d').togregorian().date()
        to_date = j_to
    
    query = DisciplineScore.query.filter(DisciplineScore.student_id.in_([s.id for s in students]))
    if from_date:
        query = query.filter(DisciplineScore.date >= from_date)
    if to_date:
        query = query.filter(DisciplineScore.date <= to_date)
    
    # pagination
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 20
    total = query.count()
    disc_scores = query.offset(offset).limit(per_page).all()
    
    # شمسی
    for disc in disc_scores:
        jdate = jdatetime.date.fromgregorian(date=disc.date).strftime('%Y/%m/%d')
        disc.jdate = jdate
    
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
    
    return render_template('manage_discipline.html', cls=cls, students=students, disciplines=disciplines, disc_scores=disc_scores, pagination=pagination, from_date_str=from_date_str, to_date_str=to_date_str)
@teacher_bp.route('/discipline/add', methods=['POST'])
@login_required(role='teacher')
def add_discipline():
    student_id = request.form.get('student_id')
    discipline_type = request.form.get('discipline_type')
    score = request.form.get('score')
    date_str = request.form.get('date')  # شمسی
    class_id = request.form.get('class_id')
    if all([student_id, discipline_type, score, date_str, class_id]):
        try:
            # فیکس: parse شمسی
            date_parts = date_str.split('/')
            if len(date_parts) != 3 or not all(part.isdigit() for part in date_parts):
                raise ValueError("فرمت تاریخ نامعتبر. از YYYY/MM/DD استفاده کنید.")
            year, month, day = map(int, date_parts)
            jdate = jdatetime.date(year, month, day)
            gdate = jdate.togregorian()
            
            disc = DisciplineScore(
                student_id=int(student_id),
                discipline_type=discipline_type,
                score=float(score),
                date=gdate,
                teacher_id=session['user_id']
            )
            db.session.add(disc)
            db.session.commit()
            flash('نمره بی‌انضباطی ثبت شد', 'success')
        except ValueError as ve:
            db.session.rollback()
            flash(f'خطا در تاریخ شمسی: {str(ve)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('teacher.manage_discipline', class_id=class_id))

@teacher_bp.route('/discipline/delete/<int:disc_id>')
@login_required(role='teacher')
def delete_discipline(disc_id):
    disc = DisciplineScore.query.get_or_404(disc_id)
    if disc.teacher_id != session['user_id']:
        flash('دسترسی ندارید', 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    class_id = Student.query.get(disc.student_id).class_id
    try:
        db.session.delete(disc)
        db.session.commit()
        flash('نمره بی‌انضباطی حذف شد', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطا: {str(e)}', 'error')
    return redirect(url_for('teacher.manage_discipline', class_id=class_id))

# API endpoints
@teacher_bp.route('/api/subjects')
@login_required(role='teacher')
def api_teacher_subjects():
    teacher = Teacher.query.get(session['user_id'])
    subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    result = []
    for subject in subjects:
        result.append({
            'id': subject.id,
            'name': subject.name,
            'class_name': subject.class_.name,
            'grade_name': subject.class_.grade.name
        })
    return jsonify(result)

@teacher_bp.route('/api/students/<int:class_id>')
@login_required(role='teacher')
def api_get_students(class_id):
    students = Student.query.filter_by(class_id=class_id).all()
    result = []
    for student in students:
        result.append({
            'id': student.id,
            'student_id': student.student_id,
            'first_name': student.first_name,
            'last_name': student.last_name
        })
    return jsonify(result)
