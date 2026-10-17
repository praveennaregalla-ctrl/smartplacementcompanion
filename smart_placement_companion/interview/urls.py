from django.urls import path
from . import views

app_name = 'interview'

urlpatterns = [
    path('', views.predictor, name='interview_root'),
    path('predictor/', views.predictor, name='predictor'),
    path('mock/', views.mock_interview, name='mock_interview'),
    path('preparation/', views.interview_preparation, name='interview_preparation'),
    path('practice-session/', views.practice_session, name='practice_session'),
    path('practice/', views.practice_lab, name='practice_lab'),
]
