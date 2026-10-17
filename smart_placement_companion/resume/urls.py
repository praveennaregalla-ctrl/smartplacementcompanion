from django.urls import path
from . import views

app_name = 'resume'

urlpatterns = [
    path('', views.analyze_resume, name='resume_root'),
    path('analyze/', views.analyze_resume, name='analyze_resume'),
    path('analyze/<int:student_id>/', views.analyze_resume, name='analyze_student_resume'),
    path('history/<int:student_id>/', views.analysis_history, name='analysis_history'),
]
