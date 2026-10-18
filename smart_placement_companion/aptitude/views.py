import random
from datetime import timedelta
from hashlib import sha256

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.decorators import role_required
from .models import AptitudeQuestion, AptitudeTestAttempt


def _get_owner_key(request):
    if not request.session.session_key:
        request.session.save()
    return sha256(request.session.session_key.encode()).hexdigest()


def _snapshot_question(question):
    return {
        'id': question.id,
        'title': question.title,
        'prompt': question.prompt,
        'category': question.get_category_display(),
        'difficulty': question.get_difficulty_display(),
        'options': question.options if isinstance(question.options, list) else [],
        'correct_answer': question.correct_answer,
        'explanation': question.explanation,
    }


def _finish_attempt(attempt, now=None):
    if attempt.is_completed:
        return attempt
    attempt.score = sum(
        1 for question in attempt.questions
        if AptitudeQuestion._normalize_answer(question['correct_answer'])
        == AptitudeQuestion._normalize_answer(attempt.answers.get(str(question['id']), ''))
    )
    attempt.completed_at = now or timezone.now()
    attempt.save(update_fields=['score', 'completed_at'])
    return attempt


@role_required(['admin', 'student'])
def practice_session(request):
    selected_category = request.GET.get('category', '').strip()
    selected_difficulty = request.GET.get('difficulty', '').strip()
    questions = AptitudeQuestion.objects.filter(is_active=True)

    category_values = {value for value, _ in AptitudeQuestion.CATEGORY_CHOICES}
    difficulty_values = {value for value, _ in AptitudeQuestion.DIFFICULTY_CHOICES}
    if selected_category in category_values:
        questions = questions.filter(category=selected_category)
    else:
        selected_category = ''
    if selected_difficulty in difficulty_values:
        questions = questions.filter(difficulty=selected_difficulty)
    else:
        selected_difficulty = ''

    if request.method == 'POST':
        question = get_object_or_404(
            questions,
            id=request.POST.get('question_id'),
        )
        selected_answer = request.POST.get('selected_answer', '').strip()
        return render(request, 'aptitude/practice_result.html', {
            'question': question,
            'selected_answer': selected_answer,
            'is_correct': question.is_correct_answer(selected_answer),
            'categories': AptitudeQuestion.CATEGORY_CHOICES,
            'selected_category': selected_category,
        })

    question = questions.order_by('?').first()
    return render(request, 'aptitude/practice_lab.html', {
        'question': question,
        'question_count': questions.count(),
        'selected_category': selected_category,
        'selected_difficulty': selected_difficulty,
        'categories': AptitudeQuestion.CATEGORY_CHOICES,
        'difficulties': AptitudeQuestion.DIFFICULTY_CHOICES,
    })


@role_required(['admin', 'student'])
def practice_lab(request):
    return practice_session(request)


@role_required(['admin', 'student'])
def test_home(request):
    question_count = AptitudeQuestion.objects.filter(
        is_active=True,
    ).exclude(correct_answer='').count()
    test_question_count = min(question_count, AptitudeTestAttempt.QUESTION_COUNT)
    return render(request, 'aptitude/test_home.html', {
        'question_count': question_count,
        'test_question_count': test_question_count,
        'duration_minutes': test_question_count,
        'target_question_count': AptitudeTestAttempt.QUESTION_COUNT,
    })


@role_required(['admin', 'student'])
@require_POST
def start_test(request):
    available_questions = list(
        AptitudeQuestion.objects.filter(is_active=True)
        .exclude(correct_answer='')
    )
    selected_questions = random.sample(
        available_questions,
        min(len(available_questions), AptitudeTestAttempt.QUESTION_COUNT),
    )
    if not selected_questions:
        messages.error(request, 'There are no active questions available for a test yet.')
        return redirect('aptitude:test_home')

    now = timezone.now()
    duration_seconds = len(selected_questions) * 60
    attempt = AptitudeTestAttempt.objects.create(
        owner_key=_get_owner_key(request),
        questions=[_snapshot_question(question) for question in selected_questions],
        total_questions=len(selected_questions),
        duration_seconds=duration_seconds,
        started_at=now,
        expires_at=now + timedelta(seconds=duration_seconds),
    )
    return redirect('aptitude:test_attempt', attempt_id=attempt.id)


@role_required(['admin', 'student'])
def test_attempt(request, attempt_id):
    attempt = get_object_or_404(
        AptitudeTestAttempt,
        id=attempt_id,
        owner_key=_get_owner_key(request),
    )
    if attempt.is_completed:
        return redirect('aptitude:test_result', attempt_id=attempt.id)

    now = timezone.now()
    if now >= attempt.expires_at:
        _finish_attempt(attempt, now=attempt.expires_at)
        return redirect('aptitude:test_result', attempt_id=attempt.id)

    index = request.GET.get('q', '0')
    try:
        current_index = int(index)
    except (TypeError, ValueError):
        current_index = 0
    current_index = max(0, min(current_index, attempt.total_questions - 1))

    if request.method == 'POST':
        submitted_index = request.POST.get('question_index', '')
        try:
            submitted_index = int(submitted_index)
        except (TypeError, ValueError):
            submitted_index = -1

        if 0 <= submitted_index < attempt.total_questions:
            if 'selected_answer' in request.POST:
                question_id = str(attempt.questions[submitted_index]['id'])
                attempt.answers[question_id] = request.POST.get('selected_answer', '').strip()
                attempt.save(update_fields=['answers'])

        if request.POST.get('action') == 'finish':
            _finish_attempt(attempt)
            return redirect('aptitude:test_result', attempt_id=attempt.id)

        if timezone.now() >= attempt.expires_at:
            _finish_attempt(attempt, now=attempt.expires_at)
            return redirect('aptitude:test_result', attempt_id=attempt.id)

        try:
            next_index = int(request.POST.get('next_index', submitted_index))
        except (TypeError, ValueError):
            next_index = submitted_index
        current_index = max(0, min(next_index, attempt.total_questions - 1))
        return redirect(f"{reverse('aptitude:test_attempt', args=[attempt.id])}?q={current_index}")

    return render(request, 'aptitude/test_attempt.html', {
        'attempt': attempt,
        'question': attempt.questions[current_index],
        'current_index': current_index,
        'question_number': current_index + 1,
        'selected_answer': attempt.answers.get(str(attempt.questions[current_index]['id']), ''),
        'answers': attempt.answers,
        'questions': attempt.questions,
        'question_nav': [
            {
                'number': index + 1,
                'index': index,
                'answered': str(question['id']) in attempt.answers and bool(attempt.answers[str(question['id'])]),
                'current': index == current_index,
            }
            for index, question in enumerate(attempt.questions)
        ],
        'remaining_seconds': max(0, int((attempt.expires_at - now).total_seconds())),
    })


@role_required(['admin', 'student'])
def test_result(request, attempt_id):
    attempt = get_object_or_404(
        AptitudeTestAttempt,
        id=attempt_id,
        owner_key=_get_owner_key(request),
    )
    if not attempt.is_completed:
        return redirect('aptitude:test_attempt', attempt_id=attempt.id)

    review = [
        {
            **question,
            'selected_answer': attempt.answers.get(str(question['id']), ''),
            'is_correct': (
                AptitudeQuestion._normalize_answer(question['correct_answer'])
                == AptitudeQuestion._normalize_answer(attempt.answers.get(str(question['id']), ''))
            ),
        }
        for question in attempt.questions
    ]
    return render(request, 'aptitude/test_result.html', {
        'attempt': attempt,
        'review': review,
        'percentage': round((attempt.score / attempt.total_questions) * 100) if attempt.total_questions else 0,
        'elapsed_minutes': max(1, int((attempt.completed_at - attempt.started_at).total_seconds() // 60)),
    })
