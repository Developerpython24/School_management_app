from io import BytesIO
import pandas as pd
import jdatetime
from flask import send_file  # ← اضافه کن (برای دانلود اکسل)
from models import Score, SkillScore, Student, Class

def generate_excel_report(student, scores, skills, period):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if scores:
            scores_data = []
            for score in scores:
                jdate = jdatetime.date.fromgregorian(date=score.date)
                scores_data.append({
                    'تاریخ': jdate.strftime('%Y/%m/%d'),
                    'روز هفته': score.weekday,
                    'درس': score.subject_ref.name,
                    'نمره': score.score
                })
            df_scores = pd.DataFrame(scores_data)
            df_scores.to_excel(writer, sheet_name='نمرات درسی', index=False)
        if skills:
            skills_data = []
            for skill in skills:
                jdate = jdatetime.date.fromgregorian(date=skill.date)
                skills_data.append({
                    'تاریخ': jdate.strftime('%Y/%m/%d'),
                    'مهارت': skill.skill_name,
                    'نمره': skill.score
                })
            df_skills = pd.DataFrame(skills_data)
            df_skills.to_excel(writer, sheet_name='نمرات مهارتی', index=False)
    output.seek(0)
    filename = f'report_{student.first_name}_{student.last_name}_{period}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

def generate_class_excel_report(class_obj, students, period, include_skills):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        class_data = []
        for student in students:
            scores = Score.query.filter_by(student_id=student.id).all()
            avg_score = sum(s.score for s in scores) / len(scores) if scores else 0
            row = {
                'کد دانش آموزی': student.student_id,
                'نام': student.first_name,
                'نام خانوادگی': student.last_name,
                'میانگین نمرات': round(avg_score, 2)
            }
            if include_skills:
                skills = SkillScore.query.filter_by(student_id=student.id).all()
                avg_skill = sum(s.score for s in skills) / len(skills) if skills else 0
                row['میانگین مهارت'] = round(avg_skill, 2)
            class_data.append(row)
        df_class = pd.DataFrame(class_data)
        df_class.to_excel(writer, sheet_name=f'کلاس {class_obj.name}', index=False)
    output.seek(0)
    filename = f'class_report_{class_obj.name}_{period}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )