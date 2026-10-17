from django.contrib import admin

from .models import AptitudeQuestion


@admin.register(AptitudeQuestion)
class AptitudeQuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'is_active')
    list_filter = ('category', 'difficulty', 'is_active')
    search_fields = ('title', 'prompt', 'category')
