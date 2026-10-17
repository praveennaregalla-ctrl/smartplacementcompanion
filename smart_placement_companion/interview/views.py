import random
import re

from django.db.models import Q
from django.shortcuts import render, get_object_or_404

from aptitude.models import AptitudeQuestion
from core.decorators import role_required
from .models import InterviewQuestion


def normalize_text(value):
    if not value:
        return ''
    return re.sub(r'[^a-z0-9\s]', ' ', value.lower()).strip()


def evaluate_answer(question, answer_text):
    raw_answer = (answer_text or '').strip()
    answer_norm = normalize_text(raw_answer)
    candidate_keywords = [k.strip() for k in (question.expected_keywords or '').split(',') if k.strip()]
    expected = [item.strip().lower() for item in candidate_keywords]

    matched_keywords = []
    for keyword in expected:
        if normalize_text(keyword) in answer_norm:
            matched_keywords.append(keyword)

    coverage = (len(matched_keywords) / len(expected)) if expected else 0
    word_count = len(raw_answer.split()) if raw_answer else 0
    length_score = min(word_count / 80, 1.0) if word_count else 0

    structure_signals = [
        'because', 'therefore', 'however', 'for example', 'first',
        'next', 'finally', 'in summary', 'this means', 'as a result'
    ]
    signal_hits = sum(1 for signal in structure_signals if signal in answer_norm)
    structure_score = min(signal_hits / 4, 1.0)

    sentence_count = max(1, len(re.findall(r'[^.!?]+[.!?]?', raw_answer)))
    clarity_score = 1.0 if word_count >= 50 and sentence_count >= 2 else 0.6 if word_count >= 25 else 0.25

    # Weighted realism: concept coverage is most important, then reasoning structure, depth, and clarity.
    score = round((coverage * 55) + (length_score * 15) + (structure_score * 15) + (clarity_score * 15))
    score = max(0, min(100, score))

    strengths = []
    if matched_keywords:
        strengths.append(f'Covered core concepts such as {", ".join(matched_keywords[:3])}.')
    if structure_score >= 0.5:
        strengths.append('Used a clear structure with explanation and causal flow.')
    if word_count >= 40:
        strengths.append('Provided enough detail to sound like a real interview answer.')

    improvements = []
    if coverage < 0.5:
        improvements.append('Add the main technical concepts tied to the question.')
    if word_count < 30:
        improvements.append('Expand your answer with more explanation and examples.')
    if structure_score < 0.5:
        improvements.append('Use a clearer structure: define it, explain the cause, and describe the solution.')

    if score >= 80:
        feedback = 'Strong answer. You explained the concept clearly and covered the main interview points.'
    elif score >= 60:
        feedback = 'Good answer. You understand the topic, but a more structured explanation would increase confidence.'
    elif score >= 40:
        feedback = 'Fair answer. You are on the right track but need more depth and better concept coverage.'
    else:
        feedback = 'Needs improvement. Focus on explaining the core concept, the process, and the practical impact.'

    return {
        'question': question,
        'user_answer': raw_answer,
        'matched': matched_keywords,
        'expected': expected,
        'score': score,
        'feedback': feedback,
        'strengths': strengths,
        'improvements': improvements,
    }


@role_required(['admin', 'student'])
def predictor(request):
    roles = InterviewQuestion.ROLE_CHOICES
    categories = InterviewQuestion.CATEGORY_CHOICES

    role = request.GET.get('role')
    category = request.GET.get('category')
    search_query = request.GET.get('q', '').strip()

    questions = InterviewQuestion.objects.all()
    if role:
        questions = questions.filter(role=role)
    if category:
        questions = questions.filter(category=category)
    if search_query:
        questions = questions.filter(
            Q(question_text__icontains=search_query) |
            Q(expected_keywords__icontains=search_query)
        )

    questions = questions.order_by('role', 'category', 'id')

    return render(request, 'interview/predictor.html', {
        'questions': questions,
        'roles': roles,
        'categories': categories,
        'selected_role': role,
        'selected_category': category,
        'search_query': search_query,
    })


@role_required(['admin', 'student'])
def mock_interview(request):
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        user_answer = request.POST.get('answer', '').strip()
        question = get_object_or_404(InterviewQuestion, id=question_id)

        result = evaluate_answer(question, user_answer)
        return render(request, 'interview/mock_results.html', result)

    role = request.GET.get('role', 'SOFTWARE_ENGINEER')
    category = request.GET.get('category', 'HR')
    questions = InterviewQuestion.objects.filter(role=role, category=category)
    if not questions.exists():
        questions = InterviewQuestion.objects.filter(category=category)
    if not questions.exists():
        questions = InterviewQuestion.objects.all()

    question = random.choice(questions) if questions.exists() else None

    return render(request, 'interview/mock_session.html', {
        'question': question,
        'role': role,
        'roles': InterviewQuestion.ROLE_CHOICES,
        'category': category,
        'categories': InterviewQuestion.CATEGORY_CHOICES,
    })


@role_required(['admin', 'student'])
def practice_session(request):
    selected_category = request.GET.get('category', '').strip()
    questions = AptitudeQuestion.objects.filter(is_active=True)

    if selected_category:
        questions = questions.filter(category=selected_category)

    question = None
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        selected_answer = request.POST.get('selected_answer', '').strip()
        question = get_object_or_404(AptitudeQuestion, id=question_id)

        is_correct = str(question.correct_answer).strip().lower() == selected_answer.lower()
        return render(request, 'interview/practice_result.html', {
            'question': question,
            'selected_answer': selected_answer,
            'is_correct': is_correct,
            'categories': AptitudeQuestion.CATEGORY_CHOICES,
        })

    if questions.exists():
        question = questions.order_by('?').first()

    return render(request, 'interview/practice_lab.html', {
        'question': question,
        'questions': questions[:10],
        'selected_category': selected_category,
        'categories': AptitudeQuestion.CATEGORY_CHOICES,
    })


@role_required(['admin', 'student'])
def interview_preparation(request):
    """Open the voice-based mock interview experience."""
    return mock_interview(request)


@role_required(['admin', 'student'])
def practice_lab(request):
    return practice_session(request)

