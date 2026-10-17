from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Student, Company, Placement



class StudentForm(forms.ModelForm):
    """Form for creating and editing students with validation."""
    
    cgpa = forms.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'max': '10',
        }),
        help_text='CGPA must be between 0.0 and 10.0'
    )
    
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91 9876543210'
        }),
        help_text='Optional phone number'
    )
    usn = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter USN / student ID'
        }),
        help_text='University seat number or student ID'
    )
    linkedin = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.linkedin.com/in/username'
        }),
        help_text='LinkedIn profile URL'
    )
    github = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://github.com/username'
        }),
        help_text='GitHub profile URL'
    )
    leetcode = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://leetcode.com/username'
        }),
        help_text='LeetCode profile URL'
    )
    hackerrank = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.hackerrank.com/username'
        }),
        help_text='HackerRank profile URL'
    )
    aptitude_score = forms.FloatField(
        required=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100',
            'step': '0.1'
        }),
        help_text='Aptitude score (%)'
    )
    technical_score = forms.FloatField(
        required=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100',
            'step': '0.1'
        }),
        help_text='Technical score (%)'
    )
    communication_score = forms.FloatField(
        required=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100',
            'step': '0.1'
        }),
        help_text='Communication score (%)'
    )
    overall_readiness_score = forms.FloatField(
        required=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '100',
            'step': '0.1',
            'readonly': 'readonly'
        }),
        help_text='Automatically computed as the average of aptitude, technical and communication scores'
    )
    
    class Meta:
        model = Student
        fields = ['name', 'email', 'phone', 'usn', 'headline', 'linkedin', 'github', 'leetcode', 'hackerrank', 'branch', 'cgpa', 'skills', 'bio', 'profile_picture', 'resume', 'aptitude_score', 'technical_score', 'communication_score', 'overall_readiness_score']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'student@example.com'
            }),
            'headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Aspiring Software Engineer'
            }),
            'branch': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Computer Science'
            }),
            'skills': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Python, Django, SQL'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'resume': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
        }
    
    def clean_email(self):
        """Validate email is unique."""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            # Check for existing email (excluding current instance in edit mode)
            queryset = Student.objects.filter(email=email)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError("A student with this email already exists.")
        return email
    
    def clean_phone(self):
        """Clean and validate phone number."""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove spaces and common separators
            phone = phone.replace(' ', '').replace('-', '').replace('+', '')
            if not phone.isdigit():
                raise forms.ValidationError("Phone number should contain only digits.")
            if len(phone) < 10:
                raise forms.ValidationError("Phone number should be at least 10 digits.")
        return phone


class BulkStudentImportForm(forms.Form):
    """Form for uploading an Excel or CSV file to import students in bulk."""
    file = forms.FileField(
        label='Upload Excel or CSV file',
        help_text='Accepted file types: .xlsx, .csv',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.csv'
        })
    )


class StudentPasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        label='Current password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )
    new_password = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text='Use at least 8 characters and avoid common passwords.',
    )
    confirm_password = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    def __init__(self, student, *args, **kwargs):
        self.student = student
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        password = self.cleaned_data['current_password']
        if not self.student.check_password(password):
            raise forms.ValidationError('Current password is incorrect.')
        return password

    def clean_new_password(self):
        password = self.cleaned_data['new_password']
        if self.student.usn and password.casefold() == self.student.usn.casefold():
            raise forms.ValidationError('Choose a password different from your USN.')
        try:
            validate_password(password)
        except DjangoValidationError as error:
            raise forms.ValidationError(error.messages)
        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', 'The new passwords do not match.')
        return cleaned_data

    def save(self):
        self.student.set_password(self.cleaned_data['new_password'])
        return self.student


class AccountPasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        label='Current password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )
    new_password = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    confirm_password = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    def __init__(self, account, *args, **kwargs):
        self.account = account
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        password = self.cleaned_data['current_password']
        checker = getattr(self.account, 'check_hr_password', None) or self.account.check_password
        if not checker(password):
            raise forms.ValidationError('Current password is incorrect.')
        return password

    def clean_new_password(self):
        password = self.cleaned_data['new_password']
        try:
            validate_password(password, user=self.account)
        except DjangoValidationError as error:
            raise forms.ValidationError(error.messages)
        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', 'The new passwords do not match.')
        return cleaned_data


class CompanyForm(forms.ModelForm):
    """Form for creating and editing companies with validation."""
    
    BRANCH_CHOICES = [
        ('CSE', 'Computer Science & Engineering'),
        ('ECE', 'Electronics & Communication Engineering'),
        ('ISE', 'Information Science & Engineering'),
        ('ME', 'Mechanical Engineering'),
        ('CV', 'Civil Engineering'),
        ('EEE', 'Electrical & Electronics Engineering'),
    ]

    package = forms.FloatField(
        validators=[MinValueValidator(0.0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'min': '0',
        }),
        help_text='Package in LPA (Lakhs Per Annum)'
    )
    eligibility = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe eligibility criteria for applicants'
        }),
        help_text='Optional eligibility description'
    )
    required_skills = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Python, Django, SQL'
        }),
        help_text='Comma-separated required skills'
    )
    interview_process = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe the interview process'
        }),
        help_text='Interview process details'
    )
    hiring_year = forms.IntegerField(
        required=False,
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 2026'
        }),
        help_text='Hiring year for this opportunity'
    )
    application_deadline = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Application deadline for students'
    )
    hr_contact_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'HR contact person'
        }),
        help_text='Name of the HR contact for this job posting'
    )
    hr_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'hr@example.com'
        }),
        help_text='HR login email'
    )
    hr_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Set HR login password'
        }),
        help_text='Leave empty to keep the current password'
    )
    
    min_cgpa = forms.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'max': '10',
        }),
        help_text='Minimum CGPA required (0.0 - 10.0)'
    )
    
    branch = forms.MultipleChoiceField(
        choices=BRANCH_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
        }),
        help_text='Select all applicable branches'
    )
    
    class Meta:
        model = Company
        fields = [
            'name', 'location', 'role', 'package', 'eligibility', 'required_skills',
            'interview_process', 'hiring_year', 'application_deadline', 'min_cgpa',
            'branch', 'hr_contact_name', 'hr_email', 'hr_password', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company name'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Bangalore, Mumbai'
            }),
            'role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Software Engineer'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Company description and job details...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.branch:
            # Convert comma-separated string from DB to list for the form
            self.initial['branch'] = [b.strip() for b in self.instance.branch.split(',')]
        if self.instance and self.instance.hr_email:
            self.initial['hr_email'] = self.instance.hr_email
        if self.instance and self.instance.hr_contact_name:
            self.initial['hr_contact_name'] = self.instance.hr_contact_name

    def clean_branch(self):
        # Convert list from form back to comma-separated string for DB
        branches = self.cleaned_data.get('branch')
        if branches:
            return ', '.join(branches)
        return ''

    def clean_hr_email(self):
        hr_email = self.cleaned_data.get('hr_email')
        if hr_email:
            return hr_email.strip().lower()
        return hr_email

    def save(self, commit=True):
        password = self.cleaned_data.get('hr_password')
        company = super().save(commit=False)
        if commit:
            company.save()
            if password:
                company.set_hr_password(password)
        return company

class PlacementForm(forms.ModelForm):
    """Form for updating placement status."""
    class Meta:
        model = Placement
        fields = ['status', 'interview_round', 'interview_date', 'interview_time', 'feedback', 'hr_remarks', 'offer_letter', 'notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'interview_round': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Technical Round, HR Round'
            }),
            'interview_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'interview_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Feedback from the interview panel'
            }),
            'hr_remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'HR remarks and next steps'
            }),
            'offer_letter': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add any notes about this placement...'
            }),
        }
