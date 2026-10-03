"""
Civic AI — Accounts API Views (DRF)
"""
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import login, logout
from .otp.service import OTPService
from .models import User

otp_service = OTPService()


def _normalize_mobile(mobile: str) -> str:
    if not isinstance(mobile, str) or len(mobile) > 32:
        return ''
    digits = re.sub(r'\D', '', mobile)
    if len(digits) == 10:
        return f'+91{digits}'
    elif len(digits) == 12 and digits.startswith('91'):
        return f'+{digits}'
    if not 10 <= len(digits) <= 15 or digits.startswith('0'):
        return ''
    return f'+{digits}'


class SendOTPAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        mobile_value = request.data.get('mobile_number', '')
        mobile_raw = mobile_value.strip() if isinstance(mobile_value, str) else ''
        if not mobile_raw:
            return Response({'error': 'mobile_number is required'}, status=400)
        mobile = _normalize_mobile(mobile_raw)
        if not mobile:
            return Response({'error': 'Enter a valid mobile number.'}, status=400)
        ip = request.META.get('REMOTE_ADDR')
        result = otp_service.send_otp(mobile, ip_address=ip)
        code = 200 if result['success'] else 429
        return Response(result, status=code)


class VerifyOTPAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        mobile_value = request.data.get('mobile_number', '')
        otp_value = request.data.get('otp', '')
        mobile_raw = mobile_value.strip() if isinstance(mobile_value, str) else ''
        otp = otp_value.strip() if isinstance(otp_value, str) else ''
        if not mobile_raw or not otp:
            return Response({'error': 'mobile_number and otp are required'}, status=400)
        if len(otp) != 6 or not otp.isdigit():
            return Response({'error': 'Enter a valid 6-digit OTP.'}, status=400)
        mobile = _normalize_mobile(mobile_raw)
        if not mobile:
            return Response({'error': 'Enter a valid mobile number.'}, status=400)
        ip = request.META.get('REMOTE_ADDR')
        result = otp_service.verify_otp(mobile, otp, ip_address=ip)
        if result['success']:
            user = result['user']
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return Response({
                'success': True,
                'is_new_user': result.get('is_new_user', False),
                'user': {'id': str(user.id), 'mobile': user.mobile_number, 'name': user.full_name},
            })
        return Response({'success': False, 'message': result['message']}, status=400)


class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response({'success': True})


class CurrentUserAPIView(APIView):
    def get(self, request):
        u = request.user
        return Response({
            'id': str(u.id),
            'mobile': u.mobile_number,
            'name': u.full_name,
            'preferred_language': u.preferred_language,
            'preferred_state': u.preferred_state.code if u.preferred_state else None,
            'is_profile_complete': u.is_profile_complete,
        })
