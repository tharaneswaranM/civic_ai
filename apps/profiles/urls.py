"""Civic AI — Dashboard / Profile URLs"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('setup/<int:step>/', views.profile_setup_step, name='profile_setup_step'),
]
