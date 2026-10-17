import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spc.settings')
django.setup()

from core.models import Student, Company, _normalize_branch_name

student = Student.objects.get(id=1)
company = Company.objects.get(id=1)

print('=== ELIGIBILITY CHECK ===')
print('Student: ' + student.name + ', Branch: ' + student.branch + ', CGPA: ' + str(student.cgpa))
print('Company: ' + company.name + ', Required: ' + company.branch + ', Min CGPA: ' + str(company.min_cgpa))
print('Student Skills: ' + student.skills)
print('Company Skills: ' + company.required_skills)
print()

cgpa_pass = student.cgpa >= company.min_cgpa
student_branch = _normalize_branch_name(student.branch)
company_branches = {_normalize_branch_name(b) for b in company.branches_list}
branch_pass = student_branch in company_branches

print('CGPA Check: ' + str(cgpa_pass))
print('Branch: ' + student_branch + ' in ' + str(company_branches) + ' = ' + str(branch_pass))
print('Is Eligible: ' + str(student.is_eligible_for(company)))
print()

skill_gap = student.get_skill_gap(company)
print('Matched: ' + str(skill_gap['matched']))
print('Missing: ' + str(skill_gap['missing']))
