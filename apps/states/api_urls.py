"""Civic AI — States API URLs"""
from django.urls import path
from . import views

app_name = 'api_states'

urlpatterns = [
    path('', views.states_api, name='list'),
    path('languages/', views.languages_api, name='languages'),
]
