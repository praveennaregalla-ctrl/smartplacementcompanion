from django.test import TestCase

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
