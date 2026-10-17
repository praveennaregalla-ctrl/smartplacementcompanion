from django.shortcuts import render, redirect, get_object_or_404
from core.decorators import role_required
from django.contrib import messages
from .forms import ResumeUploadForm
from .models import ResumeAnalysis
from .nlp_utils import extract_text_from_pdf, analyze_resume_logic
from core.models import Student

@role_required(['admin', 'student'])
def analyze_resume(request, student_id=None):
    student = None
    if student_id:
        student = get_object_or_404(Student, id=student_id)
        
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume_file = request.FILES['resume_file']
            
            # 1. Extract Text
            text = extract_text_from_pdf(resume_file)
            
            if not text.strip():
                messages.error(request, "Could not extract text from the PDF. Please ensure it's not an image-only PDF.")
                return render(request, 'resume/analyze.html', {'form': form, 'student': student})
            
            # 2. Analyze Logic (Hybrid approach)
            # If student is selected, we could compare against their target company, 
            # but for now, we use general technical skills.
            analysis_results = analyze_resume_logic(text)
            
            # 3. Save Analysis (if student associated)
            if not student:
                # If no student passed, maybe try to find student by email or just use first one for demo
                student = Student.objects.first()
            
            analysis = ResumeAnalysis.objects.create(
                student=student,
                score=analysis_results['score'],
                ats_score=analysis_results.get('ats_score', 0),
                grammar_score=analysis_results.get('grammar_score', 0),
                matched_skills=", ".join(analysis_results['matched']),
                missing_skills=", ".join(analysis_results['missing']),
                resume_sections=", ".join(analysis_results.get('resume_sections', [])),
                suggestions="\n".join(analysis_results['suggestions']),
                extracted_text=text
            )
            
            return render(request, 'resume/results.html', {
                'analysis': analysis,
                'results': analysis_results,
                'student': student
            })
    else:
        form = ResumeUploadForm(initial={'student_id': student_id} if student_id else {})
        
    return render(request, 'resume/analyze.html', {'form': form, 'student': student})

@role_required(['admin', 'student'])
def analysis_history(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    analyses = student.resume_analyses.all()
    return render(request, 'resume/history.html', {'student': student, 'analyses': analyses})
