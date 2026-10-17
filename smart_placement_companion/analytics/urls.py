from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard_root'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
