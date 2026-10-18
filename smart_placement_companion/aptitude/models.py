from django.db import models


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

    def __str__(self):
        return f"[{self.category}] {self.title} ({self.difficulty})"


PracticeSession = AptitudeQuestion
AptitudePractice = AptitudeQuestion
