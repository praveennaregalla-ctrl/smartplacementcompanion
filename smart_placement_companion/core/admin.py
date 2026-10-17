from django.contrib import admin
from django.db.models import Count
from .models import Student, Company, Placement, Registration

# Admin Site Configuration
admin.site.site_header = "Smart Placement Drive & Recruitment Management System – Admin Panel"
admin.site.site_title = "Smart Placement Drive Admin"
admin.site.index_title = "Welcome to Smart Placement Drive Admin Panel"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'usn', 'email', 'phone', 'branch', 'cgpa', 'overall_readiness_score', 'created_at')
    list_filter = ('branch', 'cgpa', 'overall_readiness_score', 'created_at')
    search_fields = ('name', 'email', 'phone', 'branch', 'usn')
    ordering = ('-cgpa', 'name')
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'usn', 'email', 'phone')
        }),
        ('Online Profiles', {
            'fields': ('linkedin', 'github', 'leetcode', 'hackerrank')
        }),
        ('Academic Details', {
            'fields': ('branch', 'cgpa')
        }),
        ('Readiness Scores', {
            'fields': ('aptitude_score', 'technical_score', 'communication_score', 'overall_readiness_score')
        }),
        ('Documents', {
            'fields': ('resume',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'overall_readiness_score')


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role', 'student', 'user', 'is_approved', 'created_at')
    list_filter = ('role', 'is_approved', 'created_at')
    search_fields = ('name', 'email', 'usn')
    ordering = ('-created_at',)
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Registration Details', {
            'fields': ('name', 'email', 'role', 'password', 'is_approved')
        }),
        ('Linked Accounts', {
            'fields': ('student', 'user')
        }),
        ('Profile & Skills', {
            'fields': ('phone', 'usn', 'branch', 'cgpa', 'skills', 'linkedin', 'github', 'leetcode', 'hackerrank')
        }),
        ('Readiness Scores', {
            'fields': ('aptitude_score', 'technical_score', 'communication_score', 'overall_readiness_score')
        }),
        ('Documents', {
            'fields': ('resume',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'overall_readiness_score')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'package', 'hiring_year', 'min_cgpa', 'branch', 'location', 'created_at')
    list_filter = ('branch', 'location', 'hiring_year', 'created_at')
    search_fields = ('name', 'role', 'location', 'description', 'eligibility', 'required_skills')
    ordering = ('-package', 'name')
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Company Information', {
            'fields': ('name', 'location', 'description')
        }),
        ('Job Details', {
            'fields': ('role', 'package', 'hiring_year', 'application_deadline')
        }),
        ('Eligibility Criteria', {
            'fields': ('eligibility', 'min_cgpa', 'branch', 'required_skills')
        }),
        ('Interview Process', {
            'fields': ('interview_process',)
        }),
    )
    
    readonly_fields = ('created_at',)


@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ('student', 'company', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'company', 'created_at')
    search_fields = ('student__name', 'student__email', 'company__name')
    ordering = ('-created_at',)
    list_editable = ('status',)
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Placement Details', {
            'fields': ('student', 'company')
        }),
        ('Status & Notes', {
            'fields': ('status', 'interview_round', 'interview_date', 'interview_time', 'feedback', 'hr_remarks', 'offer_letter', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('student', 'company')
    
    actions = ['mark_selected', 'mark_rejected', 'mark_pending']
    
    @admin.action(description='Mark selected as SELECTED')
    def mark_selected(self, request, queryset):
        queryset.update(status='SELECTED')
    
    @admin.action(description='Mark selected as REJECTED')
    def mark_rejected(self, request, queryset):
        queryset.update(status='REJECTED')
    
    @admin.action(description='Mark selected as PENDING')
    def mark_pending(self, request, queryset):
        queryset.update(status='PENDING')
