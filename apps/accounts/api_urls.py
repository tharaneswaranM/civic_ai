"""Civic AI — Accounts API URLs (DRF)"""
from django.urls import path
from . import api_views

app_name = 'api_auth'

urlpatterns = [
    path('send-otp/', api_views.SendOTPAPIView.as_view(), name='send_otp'),
    path('verify-otp/', api_views.VerifyOTPAPIView.as_view(), name='verify_otp'),
    path('logout/', api_views.LogoutAPIView.as_view(), name='logout'),
    path('me/', api_views.CurrentUserAPIView.as_view(), name='me'),
]
