from django.db import models
from django.utils import timezone


class AptitudeQuestion(models.Model):
    CATEGORY_CHOICES = [
        ('APTITUDE', 'Aptitude'),
        ('HR', 'Human Resources'),
        ('DSA', 'Data Structures & Algorithms'),
        ('LEETCODE', 'LeetCode / Coding Problem'),
    ]
    DIFFICULTY_CHOICES = [
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='APTITUDE')
    title = models.CharField(max_length=200)
    prompt = models.TextField()
    options = models.JSONField(default=list, blank=True, help_text='Multiple-choice options for aptitude or MCQ problems')
    correct_answer = models.CharField(max_length=255, blank=True, help_text='Correct option text or expected result')
    explanation = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='MEDIUM')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'difficulty', 'id']
        db_table = 'aptitude_question'

    @staticmethod
    def _normalize_answer(value):
        return str(value or '').strip().casefold()

    def is_correct_answer(self, submitted_answer):
        normalized_expected = self._normalize_answer(self.correct_answer)
        normalized_submitted = self._normalize_answer(submitted_answer)
        return normalized_expected == normalized_submitted

    def __str__(self):
        return f"[{self.category}] {self.title} ({self.difficulty})"


class AptitudeTestAttempt(models.Model):
    QUESTION_COUNT = 50
    DURATION_SECONDS = 50 * 60

    owner_key = models.CharField(max_length=64, db_index=True)
    questions = models.JSONField(default=list)
    answers = models.JSONField(default=dict, blank=True)
    total_questions = models.PositiveSmallIntegerField(default=QUESTION_COUNT)
    duration_seconds = models.PositiveIntegerField(default=DURATION_SECONDS)
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    @property
    def is_completed(self):
        return self.completed_at is not None

    def __str__(self):
        return f"Aptitude test ({self.score}/{self.total_questions})" if self.is_completed else "Aptitude test in progress"


PracticeSession = AptitudeQuestion
AptitudePractice = AptitudeQuestion
