from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AptitudeQuestion, AptitudeTestAttempt


class AptitudeFlowTests(TestCase):
    def setUp(self):
        self.assertEqual(AptitudeQuestion.objects.count(), 50)
        AptitudeQuestion.objects.all().update(is_active=False)
        session = self.client.session
        session['role'] = 'student'
        session.save()

    def create_question(self, number):
        return AptitudeQuestion.objects.create(
            category='APTITUDE',
            title=f'Question {number}',
            prompt=f'What is {number} + 1?',
            options=[str(number), str(number + 1), str(number + 2)],
            correct_answer=str(number + 1),
            difficulty='EASY',
        )

    def test_practice_filters_by_category_and_difficulty(self):
        question = self.create_question(4)

        response = self.client.get(reverse('aptitude:practice_session'), {
            'category': 'APTITUDE',
            'difficulty': 'EASY',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['question'], question)
        self.assertEqual(response.context['question_count'], 1)

    def test_test_uses_one_question_per_minute_and_scores_saved_answers(self):
        first = self.create_question(1)
        self.create_question(5)

        response = self.client.post(reverse('aptitude:start_test'))
        attempt = AptitudeTestAttempt.objects.get()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(attempt.total_questions, 2)
        self.assertEqual(attempt.duration_seconds, 120)
        page = self.client.get(reverse('aptitude:test_attempt', args=[attempt.id]))
        self.assertEqual(page.status_code, 200)
        self.assertTemplateUsed(page, 'aptitude/test_attempt.html')

        first_index = next(
            index for index, question in enumerate(attempt.questions)
            if question['id'] == first.id
        )
        response = self.client.post(
            reverse('aptitude:test_attempt', args=[attempt.id]),
            {
                'question_index': first_index,
                'selected_answer': ' 2 ',
                'next_index': first_index,
            },
        )

        self.assertEqual(response.status_code, 302)
        attempt.refresh_from_db()
        self.assertEqual(attempt.answers[str(first.id)], '2')

        response = self.client.post(
            reverse('aptitude:test_attempt', args=[attempt.id]),
            {'question_index': first_index, 'action': 'finish'},
        )
        attempt.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(attempt.score, 1)
        self.assertTrue(attempt.is_completed)
        result = self.client.get(reverse('aptitude:test_result', args=[attempt.id]))
        self.assertEqual(result.status_code, 200)
        self.assertTemplateUsed(result, 'aptitude/test_result.html')

    def test_test_deadline_auto_completes_attempt(self):
        question = self.create_question(2)
        self.client.post(reverse('aptitude:start_test'))
        attempt = AptitudeTestAttempt.objects.get()
        attempt.answers = {str(question.id): '3'}
        attempt.expires_at = timezone.now() - timedelta(seconds=1)
        attempt.save(update_fields=['answers', 'expires_at'])

        response = self.client.get(reverse('aptitude:test_attempt', args=[attempt.id]))
        attempt.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('aptitude:test_result', args=[attempt.id]),
            fetch_redirect_response=False,
        )
        self.assertTrue(attempt.is_completed)
        self.assertEqual(attempt.score, 1)

    def test_user_cannot_view_another_session_attempt(self):
        self.create_question(3)
        self.client.post(reverse('aptitude:start_test'))
        attempt = AptitudeTestAttempt.objects.get()
        self.client.logout()
        other_client = self.client.__class__()
        session = other_client.session
        session['role'] = 'student'
        session.save()

        response = other_client.get(reverse('aptitude:test_attempt', args=[attempt.id]))

        self.assertEqual(response.status_code, 404)

    def test_50_questions_produce_a_50_minute_test(self):
        for number in range(50):
            self.create_question(number)

        home = self.client.get(reverse('aptitude:test_home'))
        response = self.client.post(reverse('aptitude:start_test'))
        attempt = AptitudeTestAttempt.objects.get()

        self.assertEqual(home.status_code, 200)
        self.assertEqual(home.context['test_question_count'], 50)
        self.assertEqual(home.context['duration_minutes'], 50)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(attempt.total_questions, 50)
        self.assertEqual(attempt.duration_seconds, 50 * 60)
