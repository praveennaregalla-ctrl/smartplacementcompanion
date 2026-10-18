from django.shortcuts import get_object_or_404, render

from core.decorators import role_required
from .models import AptitudeQuestion


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
def practice_lab(request):
    return practice_session(request)
