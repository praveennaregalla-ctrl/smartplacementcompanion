from django.urls import path

from . import views

app_name = 'aptitude'

urlpatterns = [
    path('', views.practice_session, name='practice_session'),
    path('practice/', views.practice_lab, name='practice_lab'),
    path('test/', views.test_home, name='test_home'),
    path('test/start/', views.start_test, name='start_test'),
    path('test/<int:attempt_id>/', views.test_attempt, name='test_attempt'),
    path('test/<int:attempt_id>/result/', views.test_result, name='test_result'),
]
