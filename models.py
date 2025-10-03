from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    school_name = db.Column(db.String(100), default='مدرسه متوسطه')
    principal_name = db.Column(db.String(100), default='')

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    teacher_classes = db.relationship('TeacherClass', back_populates='teacher', lazy=True, cascade='all, delete-orphan')
    subjects = db.relationship('Subject', back_populates='teacher', lazy=True)
    skill_scores = db.relationship('SkillScore', back_populates='teacher', lazy=True)
    discipline_scores = db.relationship('DisciplineScore', back_populates='teacher', lazy=True)

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    classes = db.relationship('Class', back_populates='grade', lazy=True)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)
    students = db.relationship('Student', back_populates='class_', lazy=True)
    subjects = db.relationship('Subject', back_populates='class_', lazy=True)
    class_teachers = db.relationship('TeacherClass', back_populates='class_', lazy=True, cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', back_populates='class_', lazy=True)
    grade = db.relationship('Grade', back_populates='classes')

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    class_ = db.relationship('Class', back_populates='subjects')
    teacher = db.relationship('Teacher', back_populates='subjects')
    scores = db.relationship('Score', back_populates='subject_ref')

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=True)
    parent_phone = db.Column(db.String(15), nullable=True)  # شماره والدین
    scores = db.relationship('Score', back_populates='student', lazy=True)
    skills = db.relationship('SkillScore', back_populates='student', lazy=True)
    attendances = db.relationship('Attendance', back_populates='student', lazy=True)
    discipline_scores = db.relationship('DisciplineScore', back_populates='student', lazy=True)
    grade = db.relationship('Grade')
    class_ = db.relationship('Class', back_populates='students')

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    weekday = db.Column(db.String(20), nullable=False)
    student = db.relationship('Student', back_populates='scores')
    subject_ref = db.relationship('Subject', back_populates='scores')

class SkillScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    skill_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    student = db.relationship('Student', back_populates='skills')
    teacher = db.relationship('Teacher', back_populates='skill_scores')

class TeacherClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    __table_args__ = (UniqueConstraint('teacher_id', 'class_id', name='unique_teacher_class'),)
    teacher = db.relationship('Teacher', back_populates='teacher_classes')
    class_ = db.relationship('Class', back_populates='class_teachers')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'present', 'absent', 'late'
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    student = db.relationship('Student', back_populates='attendances')
    class_ = db.relationship('Class', back_populates='attendances')
    teacher = db.relationship('Teacher', lazy='joined')

class DisciplineScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    discipline_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)  # منفی
    date = db.Column(db.Date, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    student = db.relationship('Student', back_populates='discipline_scores')
    teacher = db.relationship('Teacher', back_populates='discipline_scores')