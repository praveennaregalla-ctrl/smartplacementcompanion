from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import Student

class ResumeAnalysis(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='resume_analyses')
    score = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    ats_score = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    grammar_score = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    matched_skills = models.TextField(blank=True, help_text="Comma-separated matched skills")
    missing_skills = models.TextField(blank=True, help_text="Comma-separated missing skills")
    resume_sections = models.TextField(blank=True, help_text="Comma-separated detected resume sections")
    suggestions = models.TextField(blank=True)
    extracted_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Analysis for {self.student.name} - Score: {self.score}"
