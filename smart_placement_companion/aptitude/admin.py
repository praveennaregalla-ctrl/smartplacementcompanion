from django.contrib import admin

from .models import AptitudeQuestion, AptitudeTestAttempt


@admin.register(AptitudeQuestion)
class AptitudeQuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'is_active')
    list_filter = ('category', 'difficulty', 'is_active')
    search_fields = ('title', 'prompt', 'category')


@admin.register(AptitudeTestAttempt)
class AptitudeTestAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_questions', 'score', 'started_at', 'completed_at')
    list_filter = ('completed_at',)
    readonly_fields = (
        'owner_key',
        'questions',
        'answers',
        'total_questions',
        'duration_seconds',
        'started_at',
        'expires_at',
        'completed_at',
        'score',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
