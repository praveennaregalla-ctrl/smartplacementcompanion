from django.contrib.auth.hashers import make_password
from django.db import migrations


def seed_demo_data(apps, schema_editor):
    Student = apps.get_model('core', 'Student')
    Company = apps.get_model('core', 'Company')

    student_defaults = {
        'name': 'View Test Student',
        'branch': 'Computer Science',
        'cgpa': 8.7,
        'usn': '1AB23CS001',
        'skills': 'python, django, sql, javascript',
        'password': make_password('1AB23CS001'),
    }
    student, _ = Student.objects.using(schema_editor.connection.alias).get_or_create(
        email='student@example.com',
        defaults=student_defaults,
    )

    Company.objects.using(schema_editor.connection.alias).get_or_create(
        name='Demo Company',
        defaults={
            'location': 'Bangalore',
            'package': 18.5,
            'role': 'Software Engineer',
            'min_cgpa': 7.5,
            'branch': 'CSE, ISE',
            'required_skills': 'python, sql, django',
            'eligibility': 'Eligible for CSE/ISE students with minimum CGPA 7.5.',
        },
    )

    if student.usn != student_defaults['usn']:
        student.usn = student_defaults['usn']
    if not student.password:
        student.password = student_defaults['password']
    if student.branch != student_defaults['branch']:
        student.branch = student_defaults['branch']
    if student.cgpa != student_defaults['cgpa']:
        student.cgpa = student_defaults['cgpa']
    if student.skills != student_defaults['skills']:
        student.skills = student_defaults['skills']
    if student.name != student_defaults['name']:
        student.name = student_defaults['name']
    student.save(update_fields=['name', 'branch', 'cgpa', 'usn', 'skills', 'password'])


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0017_student_password'),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, migrations.RunPython.noop),
    ]
