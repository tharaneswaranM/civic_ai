"""Civic AI — Accounts URL Configuration"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('send-otp/', views.send_otp_view, name='send_otp'),
    path('verify/', views.verify_otp_view, name='verify_otp'),
    path('verify/submit/', views.verify_otp_submit, name='verify_otp_submit'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('setup/', views.profile_setup_view, name='profile_setup'),
]
