"""
Civic AI — OTP Service
Business logic for sending and verifying OTPs.
Separate from the provider layer to keep logic testable.
"""
import logging
import hashlib
import re
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext as _
from .providers import get_otp_provider

logger = logging.getLogger(__name__)


class OTPService:
    """
    Handles OTP generation, sending, rate limiting, and verification.
    """

    RATE_LIMIT_CACHE_PREFIX = 'otp_rate_'

    def __init__(self):
        self.provider = get_otp_provider()
        self.expiry_seconds = getattr(settings, 'OTP_EXPIRY_SECONDS', 300)
        self.max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
        self.resend_cooldown = getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60)

    def _get_rate_limit_key(self, mobile_number: str) -> str:
        return f"{self.RATE_LIMIT_CACHE_PREFIX}{mobile_number}"

    def _ip_request_key(self, ip_address):
        digest = hashlib.sha256(ip_address.encode('utf-8')).hexdigest()
        return f'otp_ip_rate_{digest}'

    def _allow_ip_request(self, ip_address):
        if not ip_address:
            return False
        limit = settings.OTP_IP_REQUEST_LIMIT
        window = settings.OTP_IP_REQUEST_WINDOW_SECONDS
        key = self._ip_request_key(ip_address)
        try:
            if cache.add(key, 1, timeout=window):
                return True
            try:
                count = cache.incr(key)
            except ValueError:
                if cache.add(key, 1, timeout=window):
                    return True
                count = cache.incr(key)
            return count <= limit
        except Exception as exc:
            logger.error('OTP IP rate limiter failed (%s)', type(exc).__name__)
            return False

    def check_resend_cooldown(self, mobile_number: str) -> int:
        """
        Returns seconds remaining before resend is allowed, or 0 if OK.
        Works reliably across all cache backends (LocMemCache, Redis, Memcached).
        """
        key = self._get_rate_limit_key(mobile_number)
        val = cache.get(key)
        if val is None:
            return 0
        try:
            remaining = int(float(val) - timezone.now().timestamp())
            return max(0, remaining)
        except (ValueError, TypeError):
            ttl = cache.ttl(key) if hasattr(cache, 'ttl') else 0
            return max(0, ttl) if ttl else 0

    def send_otp(self, mobile_number: str, purpose: str = 'login', ip_address: str = None) -> dict:
        """
        Generate and send an OTP.
        Handles rate limiting, storage, and audit.
        
        Returns:
            dict: {success, message, cooldown_seconds}
        """
        from apps.accounts.models import OTPRequest
        from apps.audit.models import AuditLog

        if (
            not isinstance(mobile_number, str)
            or not re.fullmatch(r'\+[1-9]\d{9,14}', mobile_number)
        ):
            return {'success': False, 'message': 'Enter a valid mobile number.', 'cooldown_seconds': 0}

        if ip_address and not self._allow_ip_request(ip_address):
            AuditLog.objects.create(
                event=AuditLog.EVENT_OTP_RATE_LIMITED,
                mobile_masked=self._mask_mobile(mobile_number),
                ip_address=ip_address,
                metadata={'limit': 'ip_request'},
            )
            return {
                'success': False,
                'message': 'Too many OTP requests. Please try again later.',
                'cooldown_seconds': settings.OTP_IP_REQUEST_WINDOW_SECONDS,
            }

        # Rate limit check
        cooldown = self.check_resend_cooldown(mobile_number)
        if cooldown > 0:
            return {
                'success': False,
                'message': f'Please wait {cooldown} seconds before requesting another OTP.',
                'cooldown_seconds': cooldown,
            }

        # Generate OTP and hash
        otp = self.provider.generate_otp()
        otp_hash = self.provider.hash_otp(otp)
        expires_at = timezone.now() + timedelta(seconds=self.expiry_seconds)

        # Expire any existing pending OTPs for this number
        OTPRequest.objects.filter(
            mobile_number=mobile_number,
            status=OTPRequest.STATUS_PENDING
        ).update(status=OTPRequest.STATUS_EXPIRED)

        # Create new OTP request
        otp_request = OTPRequest.objects.create(
            mobile_number=mobile_number,
            otp_hash=otp_hash,
            purpose=purpose,
            status=OTPRequest.STATUS_PENDING,
            ip_address=ip_address,
            expires_at=expires_at,
        )

        # Send via provider
        result = self.provider.send_otp(mobile_number, otp)

        if result['success']:
            # Set resend cooldown with expiry timestamp for accurate remaining-seconds calculation
            expiry_ts = timezone.now().timestamp() + self.resend_cooldown
            cache.set(
                self._get_rate_limit_key(mobile_number),
                expiry_ts,
                timeout=self.resend_cooldown
            )
            # Audit
            AuditLog.objects.create(
                event=AuditLog.EVENT_OTP_SENT,
                mobile_masked=self._mask_mobile(mobile_number),
                ip_address=ip_address,
                metadata={'purpose': purpose, 'provider': settings.OTP_PROVIDER}
            )
            return {
                'success': True,
                'message': 'OTP sent successfully.',
                'cooldown_seconds': self.resend_cooldown,
                'otp_request_id': str(otp_request.id),
            }
        else:
            otp_request.status = OTPRequest.STATUS_FAILED
            otp_request.save(update_fields=['status'])
            return {
                'success': False,
                'message': 'Failed to send OTP. Please try again.',
                'cooldown_seconds': 0,
            }

    def verify_otp(self, mobile_number: str, otp: str, ip_address: str = None) -> dict:
        """
        Verify an OTP for a mobile number.
        
        Returns:
            dict: {success, message, is_new_user}
        """
        from apps.accounts.models import OTPRequest, User
        from apps.audit.models import AuditLog

        if (
            not isinstance(mobile_number, str)
            or not re.fullmatch(r'\+[1-9]\d{9,14}', mobile_number)
            or not isinstance(otp, str)
            or not re.fullmatch(r'\d{6}', otp)
        ):
            return {'success': False, 'message': 'Enter a valid mobile number and 6-digit OTP.'}

        # Find the latest pending OTP
        try:
            otp_request = OTPRequest.objects.filter(
                mobile_number=mobile_number,
                status=OTPRequest.STATUS_PENDING,
            ).order_by('-created_at').first()

            if not otp_request:
                return {'success': False, 'message': 'No active OTP found. Please request a new one.'}

            if otp_request.is_expired():
                otp_request.status = OTPRequest.STATUS_EXPIRED
                otp_request.save(update_fields=['status'])
                return {'success': False, 'message': 'OTP has expired. Please request a new one.'}

            # Increment attempts
            otp_request.attempts += 1
            if otp_request.attempts > self.max_attempts:
                otp_request.status = OTPRequest.STATUS_EXPIRED
                otp_request.save(update_fields=['status', 'attempts'])
                AuditLog.objects.create(
                    event=AuditLog.EVENT_OTP_RATE_LIMITED,
                    mobile_masked=self._mask_mobile(mobile_number),
                    ip_address=ip_address,
                )
                return {'success': False, 'message': 'Too many attempts. Please request a new OTP.'}

            # Verify
            is_valid = self.provider.verify_otp(otp, otp_request.otp_hash)

            if is_valid:
                otp_request.status = OTPRequest.STATUS_VERIFIED
                otp_request.verified_at = timezone.now()
                otp_request.save(update_fields=['status', 'verified_at', 'attempts'])

                # Get or create user
                user, is_new = User.objects.get_or_create(mobile_number=mobile_number)

                AuditLog.objects.create(
                    user=user,
                    event=AuditLog.EVENT_OTP_VERIFIED,
                    mobile_masked=self._mask_mobile(mobile_number),
                    ip_address=ip_address,
                )
                return {
                    'success': True,
                    'message': 'OTP verified successfully.',
                    'user': user,
                    'is_new_user': is_new,
                }
            else:
                otp_request.save(update_fields=['attempts'])
                remaining = self.max_attempts - otp_request.attempts
                AuditLog.objects.create(
                    event=AuditLog.EVENT_OTP_FAILED,
                    mobile_masked=self._mask_mobile(mobile_number),
                    ip_address=ip_address,
                    metadata={'attempts_remaining': remaining}
                )
                return {
                    'success': False,
                    'message': _('Invalid OTP. %(remaining)d attempts remaining.') % {
                        'remaining': remaining,
                    },
                    'attempts_remaining': remaining,
                }

        except Exception as exc:
            logger.error('OTP verification failed (%s)', type(exc).__name__)
            return {'success': False, 'message': _('Verification failed. Please try again.')}

    def _mask_mobile(self, mobile: str) -> str:
        """Returns a masked version like +91XXXXXX7890."""
        if len(mobile) > 4:
            return mobile[:-6] + 'XXXXXX' + mobile[-4:]
        return 'XXXXXX'
