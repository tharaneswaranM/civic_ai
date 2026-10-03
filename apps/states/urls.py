"""Civic AI — States URL Configuration"""
from django.urls import path
from . import views

app_name = 'states'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('select-state/', views.select_state, name='select_state'),
    path('set-state/', views.set_state, name='set_state'),
    path('transition/<slug:slug>/', views.state_transition, name='state_transition'),
    path('select-language/', views.select_language, name='select_language'),
    path('set-language/', views.set_language, name='set_language'),
]
