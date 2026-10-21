import csv
import io
import logging
import re
from django.shortcuts import render, redirect, get_object_or_404
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q, Avg, Max, Count, Case, When, IntegerField
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Student, Company, Placement
from .forms import StudentForm, CompanyForm, PlacementForm, BulkStudentImportForm, StudentPasswordChangeForm, AccountPasswordChangeForm

try:
    import pandas as pd
except ImportError:  # pragma: no cover - optional dependency
    pd = None

try:
    import openpyxl
except ImportError:
    openpyxl = None


from functools import wraps

logger = logging.getLogger('core')


def _parse_numeric_value(value):
    """Parse numeric values from CSV imports that may include units like 'LPA'."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return 0.0

    cleaned = text.replace(',', '').replace('lpa', '').replace('LPA', '').strip()
    if cleaned.endswith('%'):
        cleaned = cleaned[:-1]

    try:
        return float(cleaned)
    except ValueError:
        match = re.search(r'[-+]?\d*\.?\d+', text)
        if match:
            return float(match.group(0))
        return 0.0


# -------------------- ACCESS CONTROL --------------------

# -------------------- ACCESS CONTROL HELPERS --------------------


def is_admin(request):
    return request.session.get('role') == 'admin' or request.user.is_authenticated


def is_student(request):
    return request.session.get('role') == 'student'


# -------------------- STUDENTS --------------------

@role_required(['admin'])
def student_list(request):
    """List all students with search and pagination for admins only."""
    query = request.GET.get('q', '').strip()

    if query:
        students = Student.objects.filter(
            Q(name__icontains=query) |
            Q(branch__icontains=query) |
            Q(email__icontains=query) |
            Q(usn__icontains=query)
        )
    else:
        students = Student.objects.all()

    students = students.order_by('id')
    total_students = students.count()
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/students.html', {
        'students': page_obj,
        'page_obj': page_obj,
        'query': query,
        'total_students': total_students,
    })


@role_required(['admin'])
def add_student(request):
    """Add a new student."""
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            logger.info(f"Student created: {student.name} (ID: {student.id})")
            messages.success(request, f"Student '{student.name}' added successfully!")
            return redirect('students')
    else:
        form = StudentForm()

    return render(request, 'core/add_student.html', {'form': form})


@role_required(['admin'])
def import_students(request):
    """Bulk import student records from XLSX or CSV."""
    if request.method == 'POST':
        form = BulkStudentImportForm(request.POST, request.FILES)
        if form.is_valid():
            upload_file = form.cleaned_data['file']
            filename = upload_file.name.lower()
            created_count = 0
            skipped_count = 0
            errors = []

            if filename.endswith('.xlsx'):
                if not openpyxl:
                    messages.error(request, 'openpyxl is required for XLSX file import. Please install it and try again.')
                    return redirect('import_students')
                workbook = openpyxl.load_workbook(io.BytesIO(upload_file.read()), data_only=True)
                sheet = workbook.active
                rows = list(sheet.iter_rows(values_only=True))
                if not rows:
                    errors.append('The uploaded spreadsheet is empty.')
                else:
                    headers = [str(cell).strip().lower() if cell is not None else '' for cell in rows[0]]
                    for row_index, row in enumerate(rows[1:], start=2):
                        row_data = {headers[i]: row[i] for i in range(len(headers)) if headers[i]}
                        success, message = _create_student_from_row(row_data)
                        if success:
                            created_count += 1
                        else:
                            skipped_count += 1
                            errors.append(f'Row {row_index}: {message}')
            elif filename.endswith('.csv'):
                file_data = io.StringIO(upload_file.read().decode('utf-8-sig'))
                reader = csv.DictReader(file_data)
                if reader.fieldnames is None:
                    errors.append('CSV file does not contain headers.')
                else:
                    for row_index, row in enumerate(reader, start=2):
                        row_data = {key.strip().lower(): value for key, value in row.items() if key}
                        success, message = _create_student_from_row(row_data)
                        if success:
                            created_count += 1
                        else:
                            skipped_count += 1
                            errors.append(f'Row {row_index}: {message}')
            else:
                messages.error(request, 'Unsupported file type. Use .xlsx or .csv.')
                return redirect('import_students')

            if created_count:
                messages.success(request, f'Successfully imported {created_count} students.')
            if skipped_count:
                messages.warning(request, f'Skipped {skipped_count} rows. {len(errors)} issue(s) found.')
            if errors:
                for error in errors[:10]:
                    messages.error(request, error)
                if len(errors) > 10:
                    messages.error(request, f'...and {len(errors) - 10} more errors. Check the file format and content.')
            return redirect('students')
    else:
        form = BulkStudentImportForm()

    return render(request, 'core/import_students.html', {
        'form': form,
    })


def _create_student_from_row(row_data):
    """Create a Student instance from a row dictionary for bulk import."""
    try:
        email = (row_data.get('email') or '').strip().lower()
        name = (row_data.get('name') or '').strip()
        branch = (row_data.get('branch') or '').strip()
        usn = (row_data.get('usn') or '').strip().upper()
        if not name or not email:
            return False, 'Missing required Name or Email.'
        if Student.objects.filter(email__iexact=email).exists():
            return False, f'Student with email {email} already exists.'
        if usn and Student.objects.filter(usn__iexact=usn).exists():
            return False, f'Student with USN {usn} already exists.'

        student = Student(
            name=name,
            email=email,
            branch=branch or 'Unknown',
            phone=(row_data.get('phone') or '').strip() or None,
            usn=usn or None,
            headline=(row_data.get('headline') or '').strip() or None,
            linkedin=(row_data.get('linkedin') or '').strip() or None,
            github=(row_data.get('github') or '').strip() or None,
            leetcode=(row_data.get('leetcode') or '').strip() or None,
            hackerrank=(row_data.get('hackerrank') or '').strip() or None,
            skills=(row_data.get('skills') or '').strip() or '',
            bio=(row_data.get('bio') or '').strip() or None,
        )

        try:
            student.cgpa = float(row_data.get('cgpa', 0) or 0.0)
        except (TypeError, ValueError):
            return False, 'Invalid CGPA value.'

        for score_field in ['aptitude_score', 'technical_score', 'communication_score']:
            try:
                setattr(student, score_field, float(row_data.get(score_field, 0) or 0.0))
            except (TypeError, ValueError):
                return False, f'Invalid value for {score_field}.'

        try:
            student.full_clean()
        except ValidationError as exc:
            errors = []
            for field, field_errors in exc.message_dict.items():
                label = 'USN' if field == 'usn' else field.replace('_', ' ').title()
                errors.append(f"{label}: {', '.join(field_errors)}")
            return False, '; '.join(errors)
        student.save()
        return True, None
    except Exception as exc:
        return False, str(exc)


@role_required(['admin'])
def edit_student(request, id):
    """Edit an existing student."""
    student = get_object_or_404(Student, id=id)

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            logger.info(f"Student updated: {student.name} (ID: {student.id})")
            messages.success(request, f"Student '{student.name}' updated successfully!")
            return redirect('students')
    else:
        form = StudentForm(instance=student)

    return render(request, 'core/edit_student.html', {'form': form, 'student': student})


@role_required(['admin'])
def delete_student(request, id):
    """Delete a student with confirmation."""
    student = get_object_or_404(Student, id=id)
    
    if request.method == 'POST':
        name = student.name
        student.delete()
        logger.info(f"Student deleted: {name} (ID: {id})")
        messages.success(request, f"Student '{name}' deleted successfully!")
        return redirect('students')
    
    return render(request, 'core/student_confirm_delete.html', {'student': student})


@role_required(['admin', 'student'])
def student_detail(request, id):
    student = get_object_or_404(Student, id=id)
    placements = student.placements.select_related('company').all()
    upcoming_companies = Company.objects.filter(
        Q(branch__icontains=student.branch) | Q(branch__icontains='all')
    ).order_by('-package', 'name')[:4]

    ai_suggestions = []
    if not student.resume:
        ai_suggestions.append('Upload a resume to improve recruiter visibility.')
    if not student.skills_list:
        ai_suggestions.append('Add your strongest skills so the system can match you with relevant roles.')
    if student.overall_readiness_score < 75:
        ai_suggestions.append('Practice more technical and aptitude questions to raise your readiness score.')
    if not placements:
        ai_suggestions.append('Apply to companies that match your branch and CGPA to start building placement history.')
    elif placements.filter(status__in=['SELECTED', 'SHORTLISTED']).exists():
        ai_suggestions.append('Keep your interview preparation sharp and follow up on shortlisted opportunities.')

    notifications = []
    if student.resume:
        notifications.append({'title': 'Resume ready', 'message': 'Your resume is uploaded and can be shared with recruiters.'})
    else:
        notifications.append({'title': 'Resume pending', 'message': 'Upload a resume to make your profile stronger.'})

    if student.skills_list:
        notifications.append({'title': 'Skills updated', 'message': 'Your skills profile is ready for recruiter matching.'})
    else:
        notifications.append({'title': 'Skills missing', 'message': 'Add your key skills to receive better company matches.'})

    if upcoming_companies.exists():
        notifications.append({'title': 'Upcoming opportunities', 'message': f'{upcoming_companies[0].name} is a strong match for your profile.'})

    context = {
        'student': student,
        'placements': placements,
        'upcoming_companies': upcoming_companies,
        'ai_suggestions': ai_suggestions,
        'notifications': notifications,
    }
    return render(request, 'core/student_detail.html', context)


# -------------------- COMPANIES --------------------

@role_required(['admin', 'student', 'hr'])
def company_list(request):
    """List recruiting companies, scoped to the signed-in company for HR users."""
    companies = Company.objects.all()
    if request.session.get('role') == 'hr':
        companies = companies.filter(pk=request.session.get('company_id'))
    
    # Pagination
    paginator = Paginator(companies, 12)  # 12 companies per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/company_list.html', {
        'companies': page_obj,
        'page_obj': page_obj,
    })


@role_required(['admin'])
def add_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():

            company = form.save()

            # Find eligible students
            students = Student.objects.filter(
                cgpa__gte=company.min_cgpa,
                branch__in=company.branches_list
            )

            emails = [s.email for s in students]

            if emails:
                send_mail(
                    'New Company Opportunity',
                    f'{company.name} is hiring for {company.role}. Package: {company.package} LPA',
                    settings.EMAIL_HOST_USER,
                    emails,
                    fail_silently=True,
                )

            return redirect('company_list')
    else:
        form = CompanyForm()

    return render(request, 'core/add_company.html', {'form': form})


@role_required(['admin', 'hr'])
def edit_company(request, id):
    """Edit a company; HR accounts may only edit their own company profile."""
    company_queryset = Company.objects.all()
    is_hr = request.session.get('role') == 'hr'
    if is_hr:
        company_queryset = company_queryset.filter(pk=request.session.get('company_id'))
    company = get_object_or_404(company_queryset, id=id)

    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if is_hr:
            form.fields.pop('hr_email', None)
            form.fields.pop('hr_password', None)
        if form.is_valid():
            form.save()
            messages.success(request, f"Company '{company.name}' updated successfully!")
            return redirect('company_list')
    else:
        form = CompanyForm(instance=company)
        if is_hr:
            form.fields.pop('hr_email', None)
            form.fields.pop('hr_password', None)

    return render(request, 'core/edit_company.html', {'form': form, 'company': company, 'is_hr': is_hr})


@role_required(['admin', 'student', 'hr'])
def company_detail(request, id):
    company_queryset = Company.objects.all()
    if request.session.get('role') == 'hr':
        company_queryset = company_queryset.filter(pk=request.session.get('company_id'))
    company = get_object_or_404(company_queryset, id=id)

    eligible_students = Student.objects.filter(
        cgpa__gte=company.min_cgpa,
        branch__in=company.branches_list
    )

    return render(request, 'core/company_detail.html', {
        'company': company,
        'students': eligible_students,
        'students_all': Student.objects.all(),
        'has_applied': Placement.objects.filter(student_id=request.session.get('student_id'), company=company).exists() if request.session.get('role') == 'student' else False
    })


@role_required(['student'])
def apply_company(request, id):
    """View for students to apply to a company."""
    if request.method != 'POST':
        return redirect('company_detail', id=id)
        
    company = get_object_or_404(Company, id=id)
    student_id = request.session.get('student_id')
    
    if not student_id:
        messages.error(request, "Student session not found. Please login again.")
        return redirect('student_login')
    
    student = get_object_or_404(Student, id=student_id)
    
    # Check eligibility
    if not student.is_eligible_for(company):
        messages.error(request, f"You are not eligible for {company.name} based on CGPA or Branch requirements.")
        return redirect('company_detail', id=id)
    
    # Create or get placement
    placement, created = Placement.objects.get_or_create(
        student=student,
        company=company,
        defaults={'status': 'APPLIED'}
    )
    
    if created:
        messages.success(request, f"Successfully applied to {company.name}!")
    else:
        messages.info(request, f"You have already applied to {company.name}.")
        
    return redirect('my_applications')


@role_required(['student'])
def my_applications(request):
    """View for students to track their applications."""
    student_id = request.session.get('student_id')
    
    if not student_id:
        messages.error(request, "Student session not found. Please login again.")
        return redirect('student_login')
    
    student = get_object_or_404(Student, id=student_id)
    applications = Placement.objects.filter(student=student).select_related('company').order_by('-created_at')
    
    return render(request, 'core/my_applications.html', {
        'student': student,
        'applications': applications
    })


@role_required(['student'])
def student_profile(request):
    """LinkedIn-style profile view for students."""
    student_id = request.session.get('student_id')
    student = get_object_or_404(Student, id=student_id)
    
    # Get all applications for the student to track within the profile
    all_applications = Placement.objects.filter(student=student).select_related('company').order_by('-created_at')
    
    return render(request, 'core/profile.html', {
        'student': student,
        'applications': all_applications
    })


@role_required(['student'])
def edit_profile(request):
    """View to edit student profile."""
    student_id = request.session.get('student_id')
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('student_profile')
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'core/edit_profile.html', {
        'form': form,
        'student': student
    })


# -------------------- ELIGIBILITY CHECKER --------------------

@role_required(['admin', 'student'])
def check_eligibility(request):
    """View to check skill gap and eligibility for a specific student and company."""
    from core.models import _normalize_branch_name
    
    student_id = request.GET.get('student_id')
    company_id = request.GET.get('company_id')
    
    student = get_object_or_404(Student, id=student_id)
    company = get_object_or_404(Company, id=company_id)
    
    # Check basic eligibility (CGPA & Branch)
    is_basic_eligible = student.is_eligible_for(company)
    
    # Check individual criteria with proper normalization
    cgpa_pass = student.cgpa >= company.min_cgpa
    student_branch = _normalize_branch_name(student.branch)
    company_branches = {_normalize_branch_name(branch) for branch in company.branches_list}
    branch_pass = student_branch in company_branches
    
    # Check Skill Gap
    skill_gap = student.get_skill_gap(company)
    
    # Calculate an overall match score
    # (matched_skills / total_required) * 100
    required_count = len(company.skills_list)
    matched_count = len(skill_gap['matched'])
    
    match_score = round((matched_count / required_count * 100)) if required_count > 0 else 100
    
    return render(request, 'core/eligibility_results.html', {
        'student': student,
        'company': company,
        'is_basic_eligible': is_basic_eligible,
        'cgpa_pass': cgpa_pass,
        'branch_pass': branch_pass,
        'skill_gap': skill_gap,
        'match_score': match_score
    })


# -------------------- ELIGIBLE STUDENTS --------------------

@role_required(['admin', 'hr'])
def company_eligible_students(request, id):
    company = get_object_or_404(Company, id=id)

    if request.session.get('role') == 'hr':
        if request.session.get('company_id') != company.id:
            messages.error(request, 'Access denied to this company.')
            return redirect('hr_dashboard')

    students = Student.objects.filter(
        cgpa__gte=company.min_cgpa,
        branch__in=company.branches_list
    )

    for student in students:
        Placement.objects.get_or_create(
            student=student,
            company=company,
            defaults={'status': 'PENDING'}
        )

    placements = Placement.objects.filter(company=company)

    return render(request, 'core/company_eligible.html', {
        'company': company,
        'placements': placements
    })


# -------------------- EMAIL FUNCTIONS --------------------

def send_selection_email(placement):
    """
    Send a professional HTML email to the student when selected for placement.
    Uses Celery for async processing in production.
    """
    from django.contrib.sites.models import Site
    
    student = placement.student
    company = placement.company
    
    try:
        # Get current site domain
        current_site = Site.objects.get_current()
        domain = current_site.domain
    except:
        domain = 'localhost:8000'
    
    # Email subject
    subject = f'Congratulations {student.name}! You have been selected at {company.name}'
    
    # Plain text version
    text_content = f"""Dear {student.name},

Congratulations! You have been SELECTED for a placement opportunity.

Selection Details:
- Company: {company.name}
- Role: {company.role}
- Package: {company.package} LPA
- Status: SELECTED

The company will contact you shortly with further details regarding the offer letter, 
joining date, and other formalities.

Once again, congratulations on this achievement! We wish you all the best in your new role.

Best regards,
Placement Cell Team
Smart Placement Companion

Visit us at: https://{domain}
"""
    
    # HTML version
    html_content = render_to_string('emails/placement_selected.html', {
        'student_name': student.name,
        'student_email': student.email,
        'company_name': company.name,
        'job_role': company.role,
        'package': company.package,
        'domain': domain,
    })
    
    # Create email message
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[student.email],
    )
    email.attach_alternative(html_content, "text/html")
    
    # Send email with error handling
    try:
        email.send()
        logger.info(f"Selection email sent to {student.email} for {company.name}")
    except Exception as e:
        logger.error(f"Failed to send email to {student.email}: {str(e)}")


def send_interview_notification(placement):
    """Send interview schedule notification to the student."""
    student = placement.student
    company = placement.company
    subject = f'Interview Scheduled: {company.name} for {company.role}'
    text_content = f"""Dear {student.name},

Your interview for {company.role} at {company.name} has been scheduled.

Interview Details:
- Date: {placement.interview_date}
- Time: {placement.interview_time}
- Round: {placement.interview_round or 'Interview'}

Please prepare accordingly and reach out to the HR team if you have any questions.

Best regards,
{company.name} HR Team
"""
    html_content = render_to_string('emails/interview_notification.html', {
        'student_name': student.name,
        'company_name': company.name,
        'job_role': company.role,
        'interview_date': placement.interview_date,
        'interview_time': placement.interview_time,
        'interview_round': placement.interview_round or 'Interview',
        'company_url': f'https://{settings.SITE_DOMAIN}' if hasattr(settings, 'SITE_DOMAIN') else 'http://localhost:8000',
    })
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[student.email],
    )
    email.attach_alternative(html_content, "text/html")
    try:
        email.send()
        logger.info(f"Interview notification sent to {student.email} for {company.name}")
    except Exception as e:
        logger.error(f"Failed to send interview notification to {student.email}: {str(e)}")


# -------------------- UPDATE PLACEMENT --------------------

@role_required(['admin', 'hr'])
def update_placement(request, id):
    """
    Update placement status - Login Required View.
    """
    placement = get_object_or_404(Placement, id=id)

    if request.session.get('role') == 'hr' and placement.company_id != request.session.get('company_id'):
        messages.error(request, 'Access denied to this placement.')
        return redirect('hr_dashboard')

    if request.method == 'POST':
        form = PlacementForm(request.POST, request.FILES, instance=placement)
        if form.is_valid():
            placement = form.save()
            
            # Send professional HTML email if selected
            if placement.status == "SELECTED":
                send_selection_email(placement)

            # Notify candidate when interview details are scheduled
            if placement.interview_date and placement.interview_time:
                send_interview_notification(placement)

            messages.success(request, f"Status updated for {placement.student.name}")
            return redirect('placements')
    else:
        form = PlacementForm(instance=placement)

    return render(request, 'core/update_placement.html', {
        'placement': placement,
        'form': form
    })


# -------------------- PLACEMENT DASHBOARD --------------------

@role_required(['admin', 'student', 'hr'])
def placement_dashboard(request):
    """Placement dashboard with optimized queries."""
    status = request.GET.get('status')
    
    # Base queryset with select_related for optimization
    base_queryset = Placement.objects.select_related('student', 'company')
    if request.session.get('role') == 'hr':
        base_queryset = base_queryset.filter(company_id=request.session.get('company_id'))
    
    if status:
        placements = base_queryset.filter(status=status)
    else:
        placements = base_queryset.all()
    
    # Single query aggregation for stats
    stats = base_queryset.aggregate(
        selected_count=Count(Case(When(status='SELECTED', then=1), output_field=IntegerField())),
        rejected_count=Count(Case(When(status='REJECTED', then=1), output_field=IntegerField())),
        pending_count=Count(Case(When(status='PENDING', then=1), output_field=IntegerField())),
        applicant_count=Count('id'),
    )
    
    # Pagination
    paginator = Paginator(placements, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'placements': page_obj,
        'page_obj': page_obj,
        **stats,
        'current_status': status,
        'is_hr': request.session.get('role') == 'hr',
    }

    return render(request, 'core/dashboard_placements.html', context)


# -------------------- NEW DASHBOARD (SaaS Style) --------------------

@role_required(['admin'])
def dashboard(request):
    """New SaaS-style dashboard home page"""
    total_students = Student.objects.count()
    total_companies = Company.objects.count()
    total_placements = Placement.objects.count()
    pending_placements = Placement.objects.filter(status='PENDING').count()
    selected_placements = Placement.objects.filter(status='SELECTED').count()
    rejected_placements = Placement.objects.filter(status='REJECTED').count()
    
    # Calculate placement rate
    if total_students > 0:
        placement_rate = round((selected_placements / total_students) * 100, 1)
    else:
        placement_rate = 0
    
    # Recent placements (last 10)
    recent_placements = Placement.objects.select_related('student', 'company').order_by('-id')[:10]
    
    # Top companies by package
    top_companies = Company.objects.order_by('-package')[:5]
    
    # Placements by status (for chart)
    status_counts = {
        'selected': selected_placements,
        'pending': pending_placements,
        'rejected': rejected_placements,
    }
    
    # Placements by branch (for chart)
    branch_placements = Placement.objects.values('student__branch').annotate(
        count=Count('id')
    ).order_by('-count')[:6]
    
    context = {
        'total_students': total_students,
        'total_companies': total_companies,
        'total_placements': total_placements,
        'pending_placements': pending_placements,
        'selected_placements': selected_placements,
        'rejected_placements': rejected_placements,
        'placement_rate': placement_rate,
        'recent_placements': recent_placements,
        'top_companies': top_companies,
        'status_counts': status_counts,
        'branch_placements': branch_placements,
    }
    
    return render(request, 'core/dashboard_home.html', context)


@role_required(['admin'])
def dashboard_students(request):
    """Dashboard students page"""
    students = Student.objects.all()
    context = {
        'students': students,
        'high_cgpa_count': students.filter(cgpa__gte=8.0).count(),
        'cse_count': students.filter(branch='CSE').count(),
        'ece_count': students.filter(branch='ECE').count(),
    }
    return render(request, 'core/dashboard_students.html', context)


@role_required(['admin'])
def dashboard_companies(request):
    """Dashboard companies page"""
    companies = Company.objects.all()
    context = {
        'companies': companies,
    }
    return render(request, 'core/dashboard_companies.html', context)


@role_required(['admin'])
def dashboard_placements(request):
    """Dashboard placements page with optimized queries."""
    # Single query for all stats
    stats = Placement.objects.aggregate(
        selected_count=Count(Case(When(status='SELECTED', then=1), output_field=IntegerField())),
        pending_count=Count(Case(When(status='PENDING', then=1), output_field=IntegerField())),
        rejected_count=Count(Case(When(status='REJECTED', then=1), output_field=IntegerField())),
    )
    
    # Paginated placements
    placements_list = Placement.objects.select_related('student', 'company').order_by('-created_at')
    paginator = Paginator(placements_list, 20)
    page_number = request.GET.get('page')
    placements = paginator.get_page(page_number)
    
    context = {
        'placements': placements,
        'page_obj': placements,
        **stats,
    }
    return render(request, 'core/dashboard_placements.html', context)


@role_required(['admin'])
def dashboard_analytics(request):
    """Dashboard analytics page"""
    return render(request, 'core/dashboard_analytics.html')


@role_required(['admin'])
def import_export(request):
    """Admin page for importing and exporting student/company data."""
    if request.method == 'POST' and request.POST.get('export') == 'students':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="students.csv"'
        writer = csv.writer(response)
        writer.writerow(['name', 'email', 'branch', 'cgpa', 'phone', 'usn', 'linkedin', 'github', 'leetcode', 'hackerrank', 'skills'])
        for student in Student.objects.all():
            writer.writerow([
                student.name,
                student.email,
                student.branch,
                student.cgpa,
                student.phone or '',
                student.usn or '',
                student.linkedin or '',
                student.github or '',
                student.leetcode or '',
                student.hackerrank or '',
                student.skills or '',
            ])
        return response

    if request.method == 'POST' and request.POST.get('export') == 'companies':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="companies.csv"'
        writer = csv.writer(response)
        writer.writerow(['name', 'location', 'role', 'package', 'min_cgpa', 'branch', 'required_skills', 'eligibility'])
        for company in Company.objects.all():
            writer.writerow([
                company.name,
                company.location,
                company.role,
                company.package,
                company.min_cgpa,
                company.branch,
                company.required_skills or '',
                company.eligibility or '',
            ])
        return response

    return render(request, 'core/import_export.html', {
        'students_count': Student.objects.count(),
        'companies_count': Company.objects.count(),
    })


@role_required(['admin'])
def import_companies(request):
    """Bulk import company records from CSV."""
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            messages.error(request, 'Please choose a CSV file to upload.')
            return redirect('import_companies')

        if not uploaded_file.name.lower().endswith('.csv'):
            messages.error(request, 'Only CSV files are supported for company import.')
            return redirect('import_companies')

        try:
            decoded_file = uploaded_file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded_file))
            created_count = 0
            for row in reader:
                name = (row.get('name') or '').strip()
                if not name:
                    continue
                if Company.objects.filter(name__iexact=name).exists():
                    continue
                company = Company(
                    name=name,
                    location=(row.get('location') or '').strip() or 'Bangalore',
                    role=(row.get('role') or '').strip() or 'Software Engineer',
                    package=_parse_numeric_value(row.get('package')),
                    min_cgpa=_parse_numeric_value(row.get('min_cgpa')),
                    branch=(row.get('branch') or '').strip() or 'CSE',
                    required_skills=(row.get('required_skills') or '').strip(),
                    eligibility=(row.get('eligibility') or '').strip(),
                )
                company.save()
                created_count += 1
            messages.success(request, f'Imported {created_count} companies successfully.')
        except Exception as exc:
            messages.error(request, f'Unable to process CSV: {exc}')
        return redirect('dashboard_companies')

    return render(request, 'core/import_companies.html')


@role_required(['admin'])
def notifications(request):
    """Admin notifications center."""
    recent_activity = [
        {'title': 'Student import completed', 'message': 'Bulk uploads can be managed from the import/export hub.'},
        {'title': 'Placement updates available', 'message': 'Recent placement changes are visible on the placements dashboard.'},
        {'title': 'Analytics refreshed', 'message': 'The analytics page shows updated summaries for admins.'},
    ]
    return render(request, 'core/notifications.html', {'recent_activity': recent_activity})


# -------------------- HOME PAGE --------------------

@role_required(['admin', 'student', 'hr'])
def home(request):
    """Home page with placement statistics and highlights."""
    if request.session.get('role') == 'hr':
        return redirect('hr_dashboard')

    total_students = Student.objects.count()
    total_companies = Company.objects.count()
    selected_placements = Placement.objects.filter(status='SELECTED').count()
    total_placements = selected_placements
    
    # Calculate placement percentage
    if total_students > 0:
        placement_percentage = round((selected_placements / total_students) * 100, 1)
    else:
        placement_percentage = 0
    
    # Recent placements (last 5)
    recent_placements = Placement.objects.select_related('student', 'company').order_by('-id')[:5]
    
    # Top companies (by package)
    top_companies = Company.objects.order_by('-package')[:5]

    student_id = request.session.get('student_id')
    student = Student.objects.filter(pk=student_id).first() if student_id else None
    student_role = request.session.get('role') == 'student'
    if student_role and student is None:
        request.session.pop('student_id', None)
        request.session.pop('role', None)
        messages.warning(request, 'Your student record could not be found. Please log in again.')
        return redirect('student_login')
    if student_id and student is None:
        request.session.pop('student_id', None)
        student_id = None
    
    context = {
        'total_students': total_students,
        'total_companies': total_companies,
        'total_placements': total_placements,
        'placement_percentage': placement_percentage,
        'recent_placements': recent_placements,
        'top_companies': top_companies,
    }

    # Add student specific data
    if request.session.get('role') == 'student' or request.session.get('student_id'):
        student_id = request.session.get('student_id')
        if student_id:
            context['student'] = student
            
            # Fetch application totals with one grouped database query.
            application_stats = Placement.objects.filter(student_id=student_id).aggregate(
                applied=Count('id', filter=Q(status='APPLIED')),
                shortlisted=Count('id', filter=Q(status='SHORTLISTED')),
                selected=Count('id', filter=Q(status='SELECTED')),
                total=Count('id'),
            )
            context['applied_count'] = application_stats['applied']
            context['shortlisted_count'] = application_stats['shortlisted']
            context['selected_count'] = application_stats['selected']
            context['my_applications_count'] = application_stats['total']
            
            # Upcoming interviews
            from django.utils import timezone
            context['upcoming_interviews'] = Placement.objects.filter(
                student_id=student_id, 
                status='SHORTLISTED',
                interview_date__gte=timezone.now().date()
            ).select_related('company').order_by('interview_date', 'interview_time')[:3]
            
            # Skill Readiness (from latest resume analysis)
            from resume.models import ResumeAnalysis
            latest_analysis = ResumeAnalysis.objects.filter(student_id=student_id).order_by('-created_at').first()
            context['latest_analysis'] = latest_analysis
            context['skill_readiness'] = latest_analysis.score if latest_analysis else 0
            
            # AI Recommendations (Demo logic)
            recommendations = []
            if latest_analysis and latest_analysis.score < 80:
                missing = latest_analysis.missing_skills.split(',')[:2]
                if missing and missing[0]:
                    recommendations.append(f"Learn {missing[0].strip().upper()} to improve your resume score.")
            
            # Check for high-package companies student is eligible for but hasn't applied to
            applied_company_ids = Placement.objects.filter(student_id=student_id).values_list('company_id', flat=True)
            eligible_not_applied = Company.objects.filter(
                min_cgpa__lte=student.cgpa,
                package__gte=6.0
            ).exclude(id__in=applied_company_ids).order_by('-package')[:2]
            
            for comp in eligible_not_applied:
                if student.branch in comp.branches_list:
                    recommendations.append(f"You are eligible for {comp.name} ({comp.package} LPA). Apply now!")
            
            if not recommendations:
                recommendations.append("Your profile looks strong! Keep practicing mock interviews.")
            
            context['ai_recommendations'] = recommendations
            context['my_recent_applications'] = Placement.objects.filter(
                student_id=student_id,
            ).select_related('company').order_by('-updated_at', '-created_at')[:5]
    
    return render(request, 'core/home.html', context)

def admin_login(request):
    """
    Custom login view that handles the 'next' parameter for redirecting
    after successful authentication.
    """
    # Handle GET request - display login form
    if request.method == "GET":
        next_param = request.GET.get('next', '')
        return render(request, "core/login.html", {'next': next_param})
    
    # Handle POST request - process login
    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            request.session.set_expiry(None if request.POST.get('remember_me') else 0)
            logger.info(f"User logged in: {username}")
            
            # Redirect to 'next' URL if provided and safe
            if next_url:
                if url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
                    return redirect(next_url)
            
            # Default redirects if no 'next' URL
            return redirect("home")

        else:
            logger.warning(f"Failed login attempt for username: {username}")
            messages.error(request, "Invalid username or password")
            # Re-render form with next parameter preserved
            return render(request, "core/login.html", {'next': next_url})

# -------------------- ENTRY SYSTEM --------------------

def welcome_page(request):
    """Entry portal with Student/Admin login options."""
    if request.session.get('role'):
        return redirect('home')
    return render(request, 'core/welcome.html')


def student_login(request):
    """Authenticate students using their unique university seat number and password."""
    if request.session.get('role'):
        return redirect('home')
        
    if request.method == "POST":
        usn = request.POST.get('usn', '').strip()
        password = request.POST.get('password', '')
        
        student = Student.objects.filter(usn__iexact=usn).first()
        if student and student.check_password(password):
            # Login successful
            request.session.set_expiry(None if request.POST.get('remember_me') else 0)
            request.session['student_id'] = student.id
            request.session['role'] = 'student'
            if student.check_password(student.usn or ''):
                request.session['must_change_student_password'] = True
                messages.warning(request, 'For your security, change your default USN password to continue.')
                return redirect('change_student_password')
            logger.info(f"Student logged in: {student.name} ({usn})")
            messages.success(request, f"Welcome back, {student.name}!")
            return redirect('home')
        logger.warning(f"Student login failed for USN: {usn}")
        messages.error(request, "Invalid USN or password.")
            
    return render(request, 'core/student_login.html')


@role_required(['student'])
def change_student_password(request):
    student = Student.objects.filter(pk=request.session.get('student_id')).first()
    if student is None:
        request.session.pop('student_id', None)
        request.session.pop('role', None)
        request.session.pop('must_change_student_password', None)
        messages.warning(request, 'Your student session expired. Please log in again.')
        return redirect('student_login')

    form = StudentPasswordChangeForm(
        student,
        request.POST or None,
    )
    if request.method == 'POST' and request.POST.get('action') == 'skip' and request.session.get('must_change_student_password'):
        request.session.pop('must_change_student_password', None)
        messages.warning(request, 'Password change skipped. Your USN is still your password.')
        return redirect('home')

    if request.method == 'POST' and form.is_valid():
        form.save()
        request.session.pop('must_change_student_password', None)
        messages.success(request, 'Your password has been changed successfully.')
        return redirect('home')

    return render(request, 'core/change_student_password.html', {
        'form': form,
        'must_change_password': request.session.get('must_change_student_password', False),
    })


@role_required(['admin', 'hr'])
def account_profile(request):
    role = request.session.get('role') or 'admin'
    if role == 'hr':
        account = Company.objects.filter(pk=request.session.get('company_id')).first()
        if account is None:
            request.session.flush()
            messages.warning(request, 'Your HR account could not be found. Please log in again.')
            return redirect('hr_login')
        profile = {
            'role_label': 'HR',
            'name': account.hr_contact_name or f'{account.name} HR',
            'email': account.hr_email,
            'organization': account.name,
        }
    else:
        if not request.user.is_authenticated:
            return redirect('login')
        account = request.user
        profile = {
            'role_label': 'Administrator',
            'name': account.get_full_name() or account.username,
            'email': account.email,
            'organization': 'Smart Placement Companion',
            'username': account.username,
        }
    return render(request, 'core/account_profile.html', {'profile': profile})


@role_required(['admin', 'hr'])
def change_account_password(request):
    role = request.session.get('role') or 'admin'
    if role == 'hr':
        account = Company.objects.filter(pk=request.session.get('company_id')).first()
        if account is None:
            request.session.flush()
            messages.warning(request, 'Your HR account could not be found. Please log in again.')
            return redirect('hr_login')
    else:
        if not request.user.is_authenticated:
            return redirect('login')
        account = request.user

    form = AccountPasswordChangeForm(account, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        password = form.cleaned_data['new_password']
        if role == 'hr':
            account.set_hr_password(password)
        else:
            account.set_password(password)
            account.save(update_fields=['password'])
            update_session_auth_hash(request, account)
        messages.success(request, 'Your password has been changed successfully.')
        return redirect('account_profile')

    return render(request, 'core/account_password_change.html', {
        'form': form,
        'role_label': 'HR' if role == 'hr' else 'Administrator',
    })


def custom_logout(request):
    """Clear session and redirect to Welcome page."""
    from django.contrib.auth import logout as django_logout
    django_logout(request)
    request.session.flush()
    messages.info(request, "You have been logged out.")
    return redirect('welcome')


def hr_login(request):
    """HR login using company HR credentials."""
    if request.session.get('role'):
        return redirect('home')

    if request.method == "POST":
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        company = Company.objects.filter(hr_email=email).first()
        if company and company.check_hr_password(password):
            request.session.set_expiry(None if request.POST.get('remember_me') else 0)
            request.session['role'] = 'hr'
            request.session['company_id'] = company.id
            messages.success(request, f"Welcome {company.hr_contact_name or company.name} HR!")
            return redirect('hr_dashboard')

        messages.error(request, "Invalid HR email or password.")

    return render(request, 'core/hr_login.html')


@role_required(['hr'])
def hr_dashboard(request):
    company_id = request.session.get('company_id')
    company = get_object_or_404(Company, id=company_id)
    placements = Placement.objects.filter(company=company).select_related('student').order_by('-created_at')
    eligible_students = company.get_eligible_students()
    upcoming_interviews = placements.filter(interview_date__gte=timezone.now().date()).order_by('interview_date')[:5]
    interview_counts = placements.values('status').annotate(count=Count('id'))
    status_counts = {item['status']: item['count'] for item in interview_counts}

    return render(request, 'core/hr_dashboard.html', {
        'company': company,
        'placements': placements,
        'eligible_students_count': eligible_students.count(),
        'upcoming_interviews': upcoming_interviews,
        'status_counts': status_counts,
    })
