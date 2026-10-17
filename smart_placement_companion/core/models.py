import re

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone


def _normalize_branch_name(value):
    """Normalize branch names so 'Computer Science' and 'CSE' are treated as equivalent."""
    if not value:
        return ''

    normalized = re.sub(r'[^a-z0-9]+', '', str(value).strip().lower())
    aliases = {
        'cse': {'cse', 'computerscience', 'computerscienceengineering', 'computerscienceandengineering'},
        'ece': {'ece', 'electronicsandcommunication', 'electronicscommunication', 'electronicsandcommunicationengineering'},
        'ise': {'ise', 'informationscience', 'informationscienceengineering', 'informationscienceandengineering'},
        'me': {'me', 'mechanical', 'mechanicalengineering'},
        'cv': {'cv', 'civil', 'civilengineering'},
        'eee': {'eee', 'electricalandelectronics', 'electricalandelectronicsengineering'},
    }

    for code, names in aliases.items():
        if normalized in names:
            return code
    return normalized


def _normalize_skill_name(value):
    """Normalize skill names so spacing/punctuation differences do not break matching."""
    if not value:
        return ''
    return re.sub(r'[^a-z0-9]+', '', str(value).strip().lower())


class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, db_index=True)
    branch = models.CharField(max_length=50, db_index=True)
    cgpa = models.FloatField(
        default=0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        db_index=True
    )
    resume = models.FileField(
        upload_to='resumes/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    usn = models.CharField(max_length=50, blank=True, null=True, unique=True, db_index=True)
    password = models.CharField(max_length=128, blank=True, help_text='Hashed student login password; initially set from the USN.')
    linkedin = models.URLField(blank=True, null=True, help_text="LinkedIn profile URL")
    github = models.URLField(blank=True, null=True, help_text="GitHub profile URL")
    leetcode = models.URLField(blank=True, null=True, help_text="LeetCode profile URL")
    hackerrank = models.URLField(blank=True, null=True, help_text="HackerRank profile URL")
    headline = models.CharField(max_length=255, blank=True, null=True, help_text="Professional headline (e.g. Aspiring Software Engineer)")
    profile_picture = models.ImageField(
        upload_to='profiles/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    skills = models.TextField(
        blank=True, 
        help_text="Comma-separated skills (e.g. python, sql, dsa)"
    )
    aptitude_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Aptitude score as a percentage"
    )
    technical_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Technical score as a percentage"
    )
    communication_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Communication score as a percentage"
    )
    overall_readiness_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Overall readiness score (average of aptitude, technical and communication)"
    )
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-cgpa', 'name']
        indexes = [
            models.Index(fields=['branch', 'cgpa']),
        ]

    def save(self, *args, **kwargs):
        if not self.password and self.usn:
            self.password = make_password(self.usn)
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'password'}
        if self.skills:
            # Normalize skills to comma-separated lowercase
            skill_list = [s.strip().lower() for s in self.skills.split(',') if s.strip()]
            self.skills = ', '.join(skill_list)

        # Keep overall readiness in sync with component scores
        self.overall_readiness_score = round(
            (self.aptitude_score + self.technical_score + self.communication_score) / 3,
            2
        )
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save(update_fields=['password'])

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.name} ({self.branch})"

    @property
    def skills_list(self):
        """Return skills as a list of normalized lowercase strings"""
        if not self.skills:
            return []
        return [s.strip().lower() for s in self.skills.split(',') if s.strip()]

    def is_eligible_for(self, company):
        """Check if student is eligible for a company based on updated CGPA, branch and skill data."""
        if self.cgpa < company.min_cgpa:
            return False

        student_branch = _normalize_branch_name(self.branch)
        company_branches = {_normalize_branch_name(branch) for branch in company.branches_list}
        return student_branch in company_branches

    def get_skill_gap(self, company):
        """Compare student skills with company required skills using normalized values."""
        student_skills_normalized = [_normalize_skill_name(skill) for skill in self.skills_list]
        required_skills = {_normalize_skill_name(skill) for skill in company.skills_list}
        required_skills_set = required_skills

        # Preserve order of student skills while filtering by required skills
        matched = [skill for skill in student_skills_normalized if skill in required_skills_set]
        missing = sorted(required_skills_set.difference(set(student_skills_normalized)))

        return {
            'matched': matched,
            'missing': missing,
            'gap_percentage': round((len(missing) / len(required_skills)) * 100) if required_skills_set else 0
        }


class Registration(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Admin'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student', db_index=True)
    password = models.CharField(
        max_length=128,
        blank=True,
        help_text='Hashed password for admin registration or optional student account access.'
    )
    student = models.ForeignKey(
        Student,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='registrations'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='registrations'
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    usn = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    branch = models.CharField(max_length=50, blank=True, null=True)
    cgpa = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        blank=True,
        null=True
    )
    resume = models.FileField(
        upload_to='registration_resumes/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    linkedin = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    leetcode = models.URLField(blank=True, null=True)
    hackerrank = models.URLField(blank=True, null=True)
    skills = models.TextField(
        blank=True,
        help_text='Comma-separated skills (e.g. python, sql, dsa)'
    )
    aptitude_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    technical_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    communication_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    overall_readiness_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['role', 'email']),
        ]

    def save(self, *args, **kwargs):
        if self.skills:
            skill_list = [s.strip().lower() for s in self.skills.split(',') if s.strip()]
            self.skills = ', '.join(skill_list)

        self.overall_readiness_score = round(
            (self.aptitude_score + self.technical_score + self.communication_score) / 3,
            2
        )
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save(update_fields=['password'])

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


class Company(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    location = models.CharField(max_length=100, default="Bangalore")
    package = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0.0)],
        db_index=True
    )
    role = models.CharField(max_length=100, default="Software Engineer")
    eligibility = models.TextField(
        blank=True,
        null=True,
        help_text="Text description of eligibility criteria for applicants."
    )
    required_skills = models.TextField(
        blank=True,
        help_text="Comma-separated required skills"
    )
    interview_process = models.TextField(
        blank=True,
        null=True,
        help_text="Description of the interview process"
    )
    hiring_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
        db_index=True
    )
    application_deadline = models.DateField(
        blank=True,
        null=True,
        help_text="Last date for students to apply"
    )
    min_cgpa = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        db_index=True
    )
    branch = models.CharField(max_length=50, db_index=True)
    description = models.TextField(blank=True, null=True)
    hr_contact_name = models.CharField(max_length=100, blank=True, null=True, help_text='HR contact person name')
    hr_email = models.EmailField(blank=True, null=True, db_index=True, help_text='HR email used for company login')
    hr_password = models.CharField(max_length=128, blank=True, help_text='Hashed HR password for company login')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-package', 'name']
        indexes = [
            models.Index(fields=['min_cgpa', 'branch']),
        ]

    def save(self, *args, **kwargs):
        if self.required_skills:
            # Normalize required skills to comma-separated lowercase
            skill_list = [s.strip().lower() for s in self.required_skills.split(',') if s.strip()]
            self.required_skills = ', '.join(skill_list)
        if self.hr_email:
            self.hr_email = self.hr_email.lower().strip()
        super().save(*args, **kwargs)

    def set_hr_password(self, raw_password):
        self.hr_password = make_password(raw_password)
        self.save(update_fields=['hr_password'])

    def check_hr_password(self, raw_password):
        if not self.hr_password:
            return False
        return check_password(raw_password, self.hr_password)

    def __str__(self):
        return f"{self.name} - {self.role}"

    @property
    def skills_list(self):
        """Return required skills as a list of normalized lowercase strings"""
        if not self.required_skills:
            return []
        return [s.strip().lower() for s in self.required_skills.split(',') if s.strip()]

    @property
    def branches_list(self):
        """Return eligible branches as a list of strings"""
        if not self.branch:
            return []
        # Handle both comma-separated and slash-separated formats
        separator = ',' if ',' in self.branch else '/'
        return [b.strip() for b in self.branch.split(separator) if b.strip()]

    def get_eligible_students(self):
        """Get all students eligible for this company based on CGPA and Branch."""
        students = Student.objects.filter(cgpa__gte=self.min_cgpa)
        eligible_ids = [student.id for student in students if student.is_eligible_for(self)]
        return Student.objects.filter(id__in=eligible_ids)


class Placement(models.Model):
    STATUS_CHOICES = [
        ('APPLIED', 'Applied'),
        ('SHORTLISTED', 'Shortlisted'),
        ('REJECTED', 'Rejected'),
        ('SELECTED', 'Selected'),
        ('PENDING', 'Pending'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='placements',
        db_index=True
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='placements',
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )
    interview_round = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Interview round or stage name (e.g. Technical, HR, Final).'
    )
    feedback = models.TextField(
        blank=True,
        null=True,
        help_text='Interviewer feedback for this placement activity.'
    )
    hr_remarks = models.TextField(
        blank=True,
        null=True,
        help_text='HR remarks for the candidate after the interview.'
    )
    interview_date = models.DateField(null=True, blank=True)
    interview_time = models.TimeField(null=True, blank=True)
    offer_letter = models.FileField(
        upload_to='offer_letters/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'company')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['company', 'status']),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.company.name} [{self.status}]"
