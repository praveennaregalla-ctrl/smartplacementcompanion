from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Entry System
    path('', views.home, name='home'),
    path('welcome/', views.welcome_page, name='welcome'),
    path('home/', views.home, name='home'),
    path('login/student/', views.student_login, name='student_login'),
    path('student/change-password/', views.change_student_password, name='change_student_password'),
    path('login/admin/', views.admin_login, name='login'),
    path('login/hr/', views.hr_login, name='hr_login'),
    path('account/profile/', views.account_profile, name='account_profile'),
    path('account/change-password/', views.change_account_password, name='change_account_password'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Students - RESTful URLs
    path('students/', views.student_list, name='students'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/import/', views.import_students, name='import_students'),
    path('students/<int:id>/', views.student_detail, name='student_detail'),
    path('students/<int:id>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:id>/delete/', views.delete_student, name='delete_student'),
    
    # Companies - RESTful URLs
    path('companies/', views.company_list, name='company_list'),
    path('companies/add/', views.add_company, name='add_company'),
    path('companies/<int:id>/', views.company_detail, name='company_detail'),
    path('companies/<int:id>/edit/', views.edit_company, name='edit_company'),
    path('companies/<int:id>/eligible/', views.company_eligible_students, name='company_eligible'),
    path('check-eligibility/', views.check_eligibility, name='check_eligibility'),
    
    # Placements
    path('placements/', views.placement_dashboard, name='placements'),
    path('placements/<int:id>/update/', views.update_placement, name='update_placement'),
    
    # Student specific
    path('companies/<int:id>/apply/', views.apply_company, name='apply_company'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('profile/', views.student_profile, name='student_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # SaaS Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/students/', views.dashboard_students, name='dashboard_students'),
    path('dashboard/companies/', views.dashboard_companies, name='dashboard_companies'),
    path('dashboard/placements/', views.dashboard_placements, name='dashboard_placements'),
    path('dashboard/analytics/', views.dashboard_analytics, name='dashboard_analytics'),
    path('dashboard/import-export/', views.import_export, name='import_export'),
    path('dashboard/import-companies/', views.import_companies, name='import_companies'),
    path('dashboard/notifications/', views.notifications, name='notifications'),
    path('hr/dashboard/', views.hr_dashboard, name='hr_dashboard'),
    
    # Legacy URL Redirects (for backward compatibility)
    path('placements/dashboard/', RedirectView.as_view(url='/dashboard/placements/', permanent=True)),
    path('placements/home/', RedirectView.as_view(url='/placements/', permanent=True)),
]