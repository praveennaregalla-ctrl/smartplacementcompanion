from django.db import models
from core.models import Student


class InterviewQuestion(models.Model):
    ROLE_CHOICES = [
        ('SOFTWARE_ENGINEER', 'Software Engineer'),
        ('DATA_ANALYST', 'Data Analyst'),
        ('WEB_DEVELOPER', 'Web Developer'),
    ]
    CATEGORY_CHOICES = [
        ('TECHNICAL', 'Technical'),
        ('HR', 'HR'),
    ]

    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    question_text = models.TextField()
    expected_keywords = models.TextField(help_text="Comma-separated keywords expected in the answer")

    def __str__(self):
        return f"{self.role} - {self.category}: {self.question_text[:50]}..."


class MockSession(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='mock_sessions')
    role = models.CharField(max_length=50)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mock for {self.student.name} - {self.role} ({self.score}%)"


# Backward-compatible aliases for older imports while the aptitude model lives in its own app.
from aptitude.models import AptitudeQuestion
PracticeSession = AptitudeQuestion
InterviewPreparation = AptitudeQuestion
PracticeQuestion = AptitudeQuestion

