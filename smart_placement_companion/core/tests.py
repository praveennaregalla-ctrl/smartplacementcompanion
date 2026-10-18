from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Student, Company, Placement


class StudentModelTests(TestCase):
    """Tests for Student model."""
    
    def setUp(self):
        self.student = Student.objects.create(
            name='John Doe',
            email='john@example.com',
            branch='Computer Science',
            cgpa=8.5,
            phone='9876543210'
        )
    
    def test_student_creation(self):
        """Test student can be created."""
        self.assertEqual(self.student.name, 'John Doe')
        self.assertEqual(self.student.email, 'john@example.com')
        self.assertEqual(self.student.cgpa, 8.5)
    
    def test_student_str(self):
        """Test student string representation."""
        self.assertEqual(str(self.student), 'John Doe (Computer Science)')
    
    def test_email_unique(self):
        """Test email must be unique."""
        with self.assertRaises(Exception):
            Student.objects.create(
                name='Jane Doe',
                email='john@example.com',  # Same email
                branch='IT',
                cgpa=9.0
            )
    
    def test_cgpa_validation(self):
        """Test CGPA validation."""
        # Valid CGPA
        student = Student.objects.create(
            name='Valid Student',
            email='valid@example.com',
            branch='CS',
            cgpa=7.5
        )
        self.assertEqual(student.cgpa, 7.5)

    def test_eligibility_matches_updated_branch_and_skills(self):
        """Eligibility should work even when the student updates branch and skills in readable form."""
        company = Company.objects.create(
            name='Skill Corp',
            location='Bangalore',
            package=10.0,
            role='Developer',
            min_cgpa=7.0,
            branch='CSE',
            required_skills='Python, Django'
        )
        student = Student.objects.create(
            name='Updated Student',
            email='updated@example.com',
            branch='Computer Science',
            cgpa=8.0,
            skills='Python, Django'
        )

        self.assertTrue(student.is_eligible_for(company))
        self.assertEqual(student.get_skill_gap(company)['matched'], ['python', 'django'])


class CompanyModelTests(TestCase):
    """Tests for Company model."""
    
    def setUp(self):
        self.company = Company.objects.create(
            name='Tech Corp',
            location='Bangalore',
            package=12.5,
            role='Software Engineer',
            min_cgpa=7.0,
            branch='Computer Science'
        )
    
    def test_company_creation(self):
        """Test company can be created."""
        self.assertEqual(self.company.name, 'Tech Corp')
        self.assertEqual(self.company.package, 12.5)
    
    def test_company_str(self):
        """Test company string representation."""
        self.assertEqual(str(self.company), 'Tech Corp - Software Engineer')
    
    def test_get_eligible_students(self):
        """Test getting eligible students."""
        student = Student.objects.create(
            name='Eligible Student',
            email='eligible@example.com',
            branch='Computer Science',
            cgpa=8.0
        )
        eligible = self.company.get_eligible_students()
        self.assertIn(student, eligible)


class PlacementModelTests(TestCase):
    """Tests for Placement model."""
    
    def setUp(self):
        self.student = Student.objects.create(
            name='Test Student',
            email='test@example.com',
            branch='CS',
            cgpa=8.0
        )
        self.company = Company.objects.create(
            name='Test Company',
            location='Mumbai',
            package=10.0,
            role='Developer',
            min_cgpa=7.0,
            branch='CS'
        )
        self.placement = Placement.objects.create(
            student=self.student,
            company=self.company,
            status='PENDING'
        )
    
    def test_placement_creation(self):
        """Test placement can be created."""
        self.assertEqual(self.placement.status, 'PENDING')
        self.assertEqual(self.placement.student, self.student)
    
    def test_placement_str(self):
        """Test placement string representation."""
        expected = 'Test Student - Test Company [PENDING]'
        self.assertEqual(str(self.placement), expected)
    
    def test_unique_together(self):
        """Test student-company combination must be unique."""
        with self.assertRaises(Exception):
            Placement.objects.create(
                student=self.student,
                company=self.company,
                status='SELECTED'
            )


class ViewTests(TestCase):
    """Tests for views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.student = Student.objects.create(
            name='View Test Student',
            email='viewtest@example.com',
            branch='CS',
            cgpa=8.0
        )
    
    def test_home_view(self):
        """Test home page loads."""
        self.client.login(username='testuser', password='testpass123')
        self.client.session['role'] = 'admin'
        self.client.session.save()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_hr_home_redirects_to_hr_dashboard(self):
        company = Company.objects.create(
            name='HR Route Company',
            location='Bangalore',
            package=5.0,
            role='Developer',
            min_cgpa=6.0,
            branch='CS',
        )
        session = self.client.session
        session['role'] = 'hr'
        session['company_id'] = company.id
        session.save()

        response = self.client.get(reverse('home'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [(reverse('hr_dashboard'), 302)])
        self.assertContains(response, 'HR Route Company HR Dashboard')

    def test_admin_account_menu_pages_and_password_change(self):
        self.client.login(username='testuser', password='testpass123')
        self.client.session['role'] = 'admin'
        self.client.session.save()

        profile_response = self.client.get(reverse('account_profile'))
        self.assertContains(profile_response, 'testuser')
        password_response = self.client.post(reverse('change_account_password'), {
            'current_password': 'testpass123',
            'new_password': 'different-secure-password-53',
            'confirm_password': 'different-secure-password-53',
        })

        self.assertRedirects(password_response, reverse('account_profile'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('different-secure-password-53'))

    def test_hr_account_menu_pages_and_password_change(self):
        company = Company.objects.create(
            name='HR Account Company',
            location='Bangalore',
            package=5.0,
            role='Developer',
            min_cgpa=6.0,
            branch='CS',
            hr_email='hr-account@example.com',
            hr_contact_name='HR Contact',
        )
        company.set_hr_password('old-hr-password-53')
        session = self.client.session
        session['role'] = 'hr'
        session['company_id'] = company.id
        session.save()

        profile_response = self.client.get(reverse('account_profile'))
        self.assertContains(profile_response, 'HR Contact')
        password_response = self.client.post(reverse('change_account_password'), {
            'current_password': 'old-hr-password-53',
            'new_password': 'different-hr-password-53',
            'confirm_password': 'different-hr-password-53',
        })

        self.assertRedirects(password_response, reverse('account_profile'))
        company.refresh_from_db()
        self.assertTrue(company.check_hr_password('different-hr-password-53'))

    def test_home_redirects_when_student_session_record_is_missing(self):
        session = self.client.session
        session['role'] = 'student'
        session['student_id'] = 999999
        session.save()

        response = self.client.get(reverse('home'))

        self.assertRedirects(response, reverse('student_login'))
        self.assertNotIn('student_id', self.client.session)
        self.assertNotIn('role', self.client.session)
    
    def test_student_list_view(self):
        """Test student list page loads."""
        self.client.login(username='testuser', password='testpass123')
        self.client.session['role'] = 'admin'
        self.client.session.save()
        response = self.client.get(reverse('students'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Test Student')

    def test_student_list_displays_usn(self):
        self.student.usn = '1AB23CS001'
        self.student.save(update_fields=['usn'])
        self.client.login(username='testuser', password='testpass123')
        self.client.session['role'] = 'admin'
        self.client.session.save()

        response = self.client.get(reverse('students'))

        self.assertContains(response, 'USN')
        self.assertContains(response, '1AB23CS001')
        dashboard_response = self.client.get(reverse('dashboard_students'))
        self.assertContains(dashboard_response, '1AB23CS001')

    def test_student_list_searches_usn_and_paginates_all_students(self):
        self.student.usn = 'SEARCHUSN001'
        self.student.save(update_fields=['usn'])
        self.client.login(username='testuser', password='testpass123')
        self.client.session['role'] = 'admin'
        self.client.session.save()

        search_response = self.client.get(reverse('students'), {'q': 'searchusn001'})
        self.assertContains(search_response, 'View Test Student')
        self.assertEqual(search_response.context['total_students'], 1)

        for index in range(21):
            Student.objects.create(
                name=f'Pagination Student {index}',
                email=f'pagination{index}@example.com',
                branch='CS',
                cgpa=7.0,
            )
        list_response = self.client.get(reverse('students'))
        self.assertContains(list_response, 'Page 1 of 2')
        second_page = self.client.get(reverse('students'), {'page': 2})
        self.assertContains(second_page, 'Pagination Student 20')

    def test_student_csv_import_skips_duplicate_usn_and_imports_new_row(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.student.usn = 'EXISTING001'
        self.student.save(update_fields=['usn'])
        self.client.login(username='testuser', password='testpass123')
        self.client.session['role'] = 'admin'
        self.client.session.save()
        csv_content = (
            'name,email,branch,cgpa,usn\n'
            'Duplicate USN,duplicate-usn@example.com,CS,8.0,existing001\n'
            'New Student,new-student@example.com,CS,8.2,NEWUSN001\n'
        )
        uploaded_file = SimpleUploadedFile(
            'students.csv', csv_content.encode('utf-8'), content_type='text/csv'
        )

        response = self.client.post(
            reverse('import_students'), {'file': uploaded_file}, follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Student.objects.filter(email='duplicate-usn@example.com').exists())
        self.assertTrue(Student.objects.filter(email='new-student@example.com', usn='NEWUSN001').exists())
        self.assertContains(response, 'Student with USN EXISTING001 already exists.')

    def test_student_login_requires_initial_usn_password_and_forces_change(self):
        self.student.usn = '1AB23CS001'
        self.student.save(update_fields=['usn'])
        login_page = self.client.get(reverse('student_login'))
        self.assertContains(login_page, 'Enter your USN')
        self.assertContains(login_page, 'name="password"')
        self.assertNotContains(login_page, 'Enter your email address')
        self.assertNotContains(login_page, 'Enter your full name')

        invalid_response = self.client.post(reverse('student_login'), {
            'usn': '1ab23cs001',
            'password': 'incorrect',
        })
        self.assertContains(invalid_response, 'Invalid USN or password.')

        response = self.client.post(reverse('student_login'), {
            'usn': '1ab23cs001',
            'password': '1AB23CS001',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [(reverse('change_student_password'), 302)])
        self.assertContains(response, 'For your security, change your default USN password to continue.')
        self.assertEqual(self.client.session['student_id'], self.student.id)
        self.assertEqual(self.client.session['role'], 'student')
        self.assertTrue(self.client.session.get('must_change_student_password'))

    def test_student_can_change_default_password(self):
        self.student.usn = '1AB23CS001'
        self.student.save(update_fields=['usn'])
        session = self.client.session
        session['student_id'] = self.student.id
        session['role'] = 'student'
        session['must_change_student_password'] = True
        session.save()

        response = self.client.post(reverse('change_student_password'), {
            'current_password': '1AB23CS001',
            'new_password': 'new-secure-password-92',
            'confirm_password': 'new-secure-password-92',
        })

        self.assertRedirects(response, reverse('home'))
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('new-secure-password-92'))
        self.assertFalse(self.student.check_password('1AB23CS001'))
        self.assertNotIn('must_change_student_password', self.client.session)

        self.client.get(reverse('logout'))
        login_response = self.client.post(reverse('student_login'), {
            'usn': '1AB23CS001',
            'password': 'new-secure-password-92',
        })
        self.assertRedirects(login_response, reverse('home'))

    def test_student_can_skip_default_password_change(self):
        self.student.usn = '1AB23CS001'
        self.student.save(update_fields=['usn'])
        session = self.client.session
        session['student_id'] = self.student.id
        session['role'] = 'student'
        session['must_change_student_password'] = True
        session.save()

        response = self.client.post(reverse('change_student_password'), {'action': 'skip'})

        self.assertRedirects(response, reverse('home'))
        self.assertTrue(self.client.session.get('role') == 'student')
        self.assertNotIn('must_change_student_password', self.client.session)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('1AB23CS001'))

    def test_student_cannot_access_student_list(self):
        """Students should not be able to view the full student directory."""
        self.client.session['role'] = 'student'
        self.client.session['student_id'] = self.student.id
        self.client.session.save()

        response = self.client.get(reverse('students'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('welcome'))

    def test_admin_dashboard_includes_management_modules(self):
        """Test the admin dashboard includes the requested management modules."""
        self.client.login(username='testuser', password='testpass123')
        self.client.session['role'] = 'admin'
        self.client.session.save()

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CSV Import / Export')
        self.assertContains(response, 'Bulk Student Upload')
        self.assertContains(response, 'Bulk Company Upload')
        self.assertContains(response, 'Placement Analytics')
        self.assertContains(response, 'Search & Filters')
        self.assertContains(response, 'User Management')
        self.assertContains(response, 'Notifications')
        self.assertContains(response, reverse('import_export'))
        self.assertContains(response, reverse('import_students'))
        self.assertContains(response, reverse('import_companies'))
        self.assertContains(response, reverse('dashboard_analytics'))
        self.assertContains(response, reverse('dashboard_students'))
        self.assertContains(response, reverse('notifications'))

    def test_company_import_parses_package_with_units(self):
        """Test company CSV import handles package values like '3.5 LPA'."""
        self.client.login(username='testuser', password='testpass123')
        self.client.session['role'] = 'admin'
        self.client.session.save()

        csv_content = 'name,location,role,package,min_cgpa,branch,required_skills,eligibility\n' \
            'Acme Corp,Bangalore,Software Engineer,3.5 LPA,7.5,CSE,Python,Django\n'
        uploaded_file = SimpleUploadedFile(
            'companies.csv',
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )

        response = self.client.post(
            reverse('import_companies'),
            {'file': uploaded_file},
            follow=False
        )

        self.assertEqual(response.status_code, 302)
        company = Company.objects.get(name='Acme Corp')
        self.assertEqual(company.package, 3.5)
        self.assertEqual(company.min_cgpa, 7.5)
    
    def test_add_student_requires_login(self):
        """Test add student requires authentication."""
        response = self.client.get(reverse('add_student'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_add_student_with_login(self):
        """Test add student works when logged in."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('add_student'))
        self.assertEqual(response.status_code, 200)
    
    def test_student_detail_view(self):
        """Test student detail page loads."""
        session = self.client.session
        session['role'] = 'student'
        session['student_id'] = self.student.id
        session.save()
        response = self.client.get(
            reverse('student_detail', args=[self.student.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Test Student')

    def test_student_detail_dashboard_sections(self):
        """Test student detail page includes the requested dashboard sections."""
        self.client.login(username='testuser', password='testpass123')
        self.client.session['role'] = 'student'
        self.client.session.save()

        response = self.client.get(
            reverse('student_detail', args=[self.student.id])
        )
        self.assertContains(response, 'Resume')
        self.assertContains(response, 'Skills')
        self.assertContains(response, 'Certifications')
        self.assertContains(response, 'Coding Profiles')
        self.assertContains(response, 'Placement History')
        self.assertContains(response, 'AI Suggestions')
        self.assertContains(response, 'Upcoming Companies')
        self.assertContains(response, 'Notifications')

    def test_student_home_dashboard_sections(self):
        """Test the student home page shows the requested dashboard sections after login."""
        self.client.login(username='testuser', password='testpass123')
        self.client.session['role'] = 'student'
        self.client.session['student_id'] = self.student.id
        self.client.session.save()

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Career Overview')
        self.assertContains(response, 'Resume')
        self.assertContains(response, 'Skills')
        self.assertContains(response, 'Certifications')
        self.assertContains(response, 'Coding Profiles')
        self.assertContains(response, 'Placement History')
        self.assertContains(response, 'AI Suggestions')
        self.assertContains(response, 'Upcoming Companies')
        self.assertContains(response, 'Notifications')


class FormTests(TestCase):
    """Tests for forms."""
    
    def test_student_form_valid(self):
        """Test valid student form."""
        from .forms import StudentForm
        form_data = {
            'name': 'Form Test',
            'email': 'formtest@example.com',
            'branch': 'CS',
            'cgpa': 8.5
        }
        form = StudentForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_student_form_invalid_cgpa(self):
        """Test student form with invalid CGPA."""
        from .forms import StudentForm
        form_data = {
            'name': 'Form Test',
            'email': 'formtest@example.com',
            'branch': 'CS',
            'cgpa': 11.0  # Invalid: > 10
        }
        form = StudentForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_student_form_duplicate_email(self):
        """Test student form with duplicate email."""
        from .forms import StudentForm
        Student.objects.create(
            name='Existing',
            email='existing@example.com',
            branch='CS',
            cgpa=8.0
        )
        form_data = {
            'name': 'New Student',
            'email': 'existing@example.com',  # Duplicate
            'branch': 'IT',
            'cgpa': 9.0
        }
        form = StudentForm(data=form_data)
        self.assertFalse(form.is_valid())


class URLTests(TestCase):
    """Tests for URL routing."""
    
    def test_urls_resolve(self):
        """Test all main URLs resolve correctly."""
        from django.urls import resolve
        
        urls_to_test = [
            ('/', 'home'),
            ('/students/', 'students'),
            ('/companies/', 'company_list'),
            ('/dashboard/', 'dashboard'),
            ('/login/', 'login'),
        ]
        
        for url, name in urls_to_test:
            resolver = resolve(url)
            self.assertEqual(resolver.url_name, name)
