"""
Civic AI — Accounts Views
Handles: Login (OTP), Registration flow, Logout.
"""
import logging
import re
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import translation
from django.contrib import messages
from django.conf import settings

from .models import User
from .otp.service import OTPService
from apps.audit.services import log_audit_event
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)

otp_service = OTPService()


def _get_client_ip(request):
    # Do not trust caller-controlled X-Forwarded-For unless a trusted proxy
    # policy has been configured explicitly.
    return request.META.get('REMOTE_ADDR')


def _normalize_mobile(mobile: str) -> str:
    """Normalize mobile number to E.164 format."""
    if not isinstance(mobile, str) or len(mobile) > 32:
        return ''
    # Remove all non-digits
    digits = re.sub(r'\D', '', mobile)
    # Handle Indian numbers
    if len(digits) == 10:
        return f'+91{digits}'
    elif len(digits) == 12 and digits.startswith('91'):
        return f'+{digits}'
    elif len(digits) == 13 and digits.startswith('091'):
        return f'+91{digits[3:]}'
    if not 10 <= len(digits) <= 15 or digits.startswith('0'):
        return ''
    return f'+{digits}'


# ─── Login / OTP Views ────────────────────────────────────────────────────────

def login_view(request):
    """Show the mobile number entry form."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    # Pre-fill state/language from session
    context = {
        'selected_state_slug': request.session.get('selected_state'),
        'selected_language': request.LANGUAGE_CODE,
        'page_title': _('Sign In'),
    }
    return render(request, 'accounts/login.html', context)


@require_POST
def send_otp_view(request):
    """Send OTP to the provided mobile number."""
    mobile_raw = request.POST.get('mobile_number', '').strip()

    if not mobile_raw:
        messages.error(request, _('Please enter your mobile number.'))
        return redirect('accounts:login')

    mobile = _normalize_mobile(mobile_raw)

    # Basic validation
    if not re.match(r'^\+\d{10,15}$', mobile):
        messages.error(request, _('Please enter a valid 10-digit mobile number.'))
        return redirect('accounts:login')

    ip = _get_client_ip(request)
    result = otp_service.send_otp(mobile, purpose='login', ip_address=ip)

    masked = f"{'*' * 6}{mobile[-4:]}"
    if result['success']:
        # Store mobile in session for OTP verification
        request.session['pending_mobile'] = mobile
        request.session['otp_cooldown'] = result.get('cooldown_seconds', 60)
        log_audit_event(AuditLog.EVENT_OTP_SENT, request=request, mobile_masked=masked)
        return redirect('accounts:verify_otp')
    else:
        event = AuditLog.EVENT_OTP_RATE_LIMITED if 'cooldown' in result.get('message', '').lower() else AuditLog.EVENT_OTP_FAILED
        log_audit_event(event, request=request, mobile_masked=masked)
        messages.error(request, result['message'])
        return redirect('accounts:login')


def verify_otp_view(request):
    """Show OTP entry form."""
    mobile = request.session.get('pending_mobile')
    if not mobile:
        messages.error(request, _('Session expired. Please start again.'))
        return redirect('accounts:login')

    context = {
        'mobile_masked': f"{'*' * 6}{mobile[-4:]}",
        'mobile_number': mobile,
        'cooldown_seconds': request.session.get('otp_cooldown', 60),
        'show_dev_otp_hint': settings.DEBUG and settings.OTP_MOCK_ALLOWED,
        'page_title': _('Verify OTP'),
    }
    return render(request, 'accounts/verify_otp.html', context)


@require_POST
def verify_otp_submit(request):
    """Verify submitted OTP and log in user."""
    mobile = request.session.get('pending_mobile')
    if not mobile:
        messages.error(request, _('Session expired. Please start again.'))
        return redirect('accounts:login')

    # Combine OTP digits (supports both 6-digit and per-digit inputs)
    otp_digits = [request.POST.get(f'otp_{i}', '') for i in range(1, 7)]
    if all(d == '' for d in otp_digits):
        otp = request.POST.get('otp', '').strip()
    else:
        otp = ''.join(otp_digits).strip()

    if not otp or len(otp) != 6 or not otp.isdigit():
        messages.error(request, _('Please enter a valid 6-digit OTP.'))
        return redirect('accounts:verify_otp')

    ip = _get_client_ip(request)
    result = otp_service.verify_otp(mobile, otp, ip_address=ip)
    masked = f"{'*' * 6}{mobile[-4:]}"

    if result['success']:
        user = result['user']
        log_audit_event(AuditLog.EVENT_LOGIN_SUCCESS, request=request, user=user, mobile_masked=masked)
        # New accounts inherit onboarding language. Returning accounts restore
        # their saved preference instead of being reset by an empty session.
        supported_languages = {code for code, _name in settings.LANGUAGES}
        if result.get('is_new_user'):
            lang = request.session.get('selected_language') or request.LANGUAGE_CODE
            if lang in supported_languages and lang != user.preferred_language:
                user.preferred_language = lang
                user.save(update_fields=['preferred_language'])
        lang = user.preferred_language
        if lang not in supported_languages:
            lang = settings.LANGUAGE_CODE
        request.session['selected_language'] = lang

        # Set preferred state from session
        state_slug = request.session.get('selected_state')
        if state_slug and not user.preferred_state:
            from apps.states.models import State
            try:
                state = State.objects.get(slug=state_slug, is_active=True)
                user.preferred_state = state
                user.save(update_fields=['preferred_state'])
            except State.DoesNotExist:
                logger.info('Selected state no longer exists for authenticated user %s', user.pk)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        # Clear pending OTP session data
        request.session.pop('pending_mobile', None)
        request.session.pop('otp_cooldown', None)

        if result.get('is_new_user') or not user.is_profile_complete:
            response = redirect('accounts:profile_setup')
        else:
            response = redirect('dashboard:home')
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            lang,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
        return response
    else:
        log_audit_event(AuditLog.EVENT_OTP_FAILED, request=request, mobile_masked=masked)
        messages.error(request, result['message'])
        return redirect('accounts:verify_otp')


@require_POST
def resend_otp_view(request):
    """Resend OTP to the mobile number."""
    mobile = request.session.get('pending_mobile')
    if not mobile:
        return JsonResponse({'success': False, 'message': 'Session expired.'})

    ip = _get_client_ip(request)
    result = otp_service.send_otp(mobile, purpose='login', ip_address=ip)

    if result['success']:
        request.session['otp_cooldown'] = result.get('cooldown_seconds', 60)

    return JsonResponse({
        'success': result['success'],
        'message': result['message'],
        'cooldown_seconds': result.get('cooldown_seconds', 0),
    })


@require_POST
def logout_view(request):
    """Log out the user."""
    if request.user.is_authenticated:
        log_audit_event(AuditLog.EVENT_LOGOUT, request=request, user=request.user)
    logout(request)
    messages.success(request, _('You have been logged out successfully.'))
    return redirect('states:landing')


@login_required
def profile_setup_view(request):
    """Redirect to multi-step profile creation."""
    return redirect('dashboard:profile_setup_step', step=1)
