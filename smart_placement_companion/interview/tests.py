from django.test import Client, TestCase
from django.urls import reverse

from aptitude.models import AptitudeQuestion
from interview.models import InterviewQuestion
from interview.views import evaluate_answer


class InterviewEvaluationTests(TestCase):
    def setUp(self):
        self.question = InterviewQuestion.objects.create(
            role='SOFTWARE_ENGINEER',
            category='TECHNICAL',
            question_text='What is a deadlock and how can it be prevented?',
            expected_keywords='mutual exclusion, hold and wait, circular wait, no preemption, resource allocation'
        )

    def test_realistic_answer_scores_well(self):
        answer = (
            'A deadlock happens when two processes each hold resources and wait for the other to release them. '
            'This is caused by mutual exclusion, hold and wait, circular wait, and no preemption. '
            'To prevent it, the system should avoid circular wait by ordering resource allocation, break hold and wait conditions, '
            'and use safe resource allocation policies to reduce the chance of deadlock.'
        )

        result = evaluate_answer(self.question, answer)

        self.assertGreater(result['score'], 60)
        self.assertIn('strong', result['feedback'].lower())
        self.assertGreater(len(result['matched']), 0)
        self.assertGreater(len(result['strengths']), 0)

    def test_short_or_vague_answer_scores_low(self):
        result = evaluate_answer(self.question, 'Deadlock is bad and it happens in systems.')

        self.assertLess(result['score'], 50)
        self.assertGreater(len(result['improvements']), 0)


class AptitudeQuestionModelTests(TestCase):
    def test_aptitude_question_creation(self):
        question = AptitudeQuestion.objects.create(
            category='APTITUDE',
            title='Percentage Problem',
            prompt='If 20% of a number is 45, what is the number?',
            options=['90', '180', '225', '250'],
            correct_answer='225',
            difficulty='MEDIUM',
            explanation='20% of 225 is 45, so the number is 225.'
        )

        self.assertEqual(question.category, 'APTITUDE')
        self.assertEqual(question.correct_answer, '225')
        self.assertIn('percentage', question.title.lower())
        self.assertTrue(question.is_correct_answer(' 225 '))
        self.assertFalse(question.is_correct_answer('180'))


class AptitudePracticeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        session = self.client.session
        session['role'] = 'student'
        session.save()

    def test_practice_page_uses_aptitude_template(self):
        AptitudeQuestion.objects.create(
            category='APTITUDE',
            title='Average Speed',
            prompt='A cyclist travels 30 km in 2 hours and 20 km in 1 hour. What is the average speed?',
            options=['20 km/h', '25 km/h', '30 km/h', '35 km/h'],
            correct_answer='25 km/h',
            difficulty='MEDIUM',
        )

        response = self.client.get(reverse('aptitude:practice_session'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'aptitude/practice_lab.html')
