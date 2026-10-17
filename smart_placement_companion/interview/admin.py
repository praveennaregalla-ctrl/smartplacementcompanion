from django.contrib import admin

from .models import InterviewQuestion, MockSession


@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ('role', 'category', 'question_text')
    search_fields = ('role', 'category', 'question_text')


@admin.register(MockSession)
class MockSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'role', 'score', 'total_questions', 'created_at')
    list_filter = ('role', 'created_at')
