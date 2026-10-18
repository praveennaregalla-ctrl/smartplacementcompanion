from django.urls import path

from . import views

app_name = 'aptitude'

urlpatterns = [
    path('', views.practice_session, name='practice_session'),
    path('practice/', views.practice_lab, name='practice_lab'),
]
