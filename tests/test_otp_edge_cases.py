"""OTP lifecycle edge cases using local providers only."""
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.accounts.models import OTPRequest
from apps.accounts.otp.providers import BaseOTPProvider
from apps.accounts.otp.service import OTPService


class SequenceOTPProvider(BaseOTPProvider):
    """Deterministic in-memory provider for OTP lifecycle tests."""
    def __init__(self, codes):
        self.codes = iter(codes)
        self.sent = []

    def generate_otp(self):
        return next(self.codes)

    def send_otp(self, mobile_number, otp):
        self.sent.append((mobile_number, otp))
        return {'success': True, 'message': 'sent', 'provider_reference': 'test'}


class OTPLifecycleEdgeCaseTests(TestCase):
    mobile = '+919876543210'

    def setUp(self):
        cache.clear()
        self.service = OTPService()

    @override_settings(OTP_EXPIRY_SECONDS=-1)
    def test_expired_otp_is_rejected_and_marked_expired(self):
        self.service = OTPService()
        sent = self.service.send_otp(self.mobile)
        self.assertTrue(sent['success'])

        result = self.service.verify_otp(self.mobile, '123456')
        request = OTPRequest.objects.get(mobile_number=self.mobile)
        self.assertFalse(result['success'])
        self.assertEqual(request.status, OTPRequest.STATUS_EXPIRED)

    @override_settings(OTP_MAX_ATTEMPTS=2)
    def test_attempt_limit_expires_otp_after_configured_number_of_failures(self):
        self.service = OTPService()
        self.service.send_otp(self.mobile)

        first = self.service.verify_otp(self.mobile, '000000')
        second = self.service.verify_otp(self.mobile, '000000')
        third = self.service.verify_otp(self.mobile, '000000')
        request = OTPRequest.objects.get(mobile_number=self.mobile)

        self.assertEqual(first['attempts_remaining'], 1)
        self.assertEqual(second['attempts_remaining'], 0)
        self.assertFalse(third['success'])
        self.assertIn('Too many attempts', third['message'])
        self.assertEqual(request.status, OTPRequest.STATUS_EXPIRED)
        self.assertEqual(request.attempts, 3)

    @override_settings(OTP_RESEND_COOLDOWN_SECONDS=60)
    def test_resend_is_blocked_during_cooldown_and_allowed_after_expiry(self):
        self.service = OTPService()
        first = self.service.send_otp(self.mobile)
        during_cooldown = self.service.send_otp(self.mobile)
        self.assertTrue(first['success'])
        self.assertFalse(during_cooldown['success'])
        self.assertGreater(during_cooldown['cooldown_seconds'], 0)
        self.assertEqual(OTPRequest.objects.filter(mobile_number=self.mobile).count(), 1)

        cache.set(
            self.service._get_rate_limit_key(self.mobile),
            timezone.now().timestamp() - 1,
            timeout=60,
        )
        after_cooldown = self.service.send_otp(self.mobile)
        self.assertTrue(after_cooldown['success'])
        requests = list(OTPRequest.objects.filter(mobile_number=self.mobile).order_by('created_at'))
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0].status, OTPRequest.STATUS_EXPIRED)
        self.assertEqual(requests[1].status, OTPRequest.STATUS_PENDING)

    def test_old_otp_is_rejected_after_resend_and_verified_otp_cannot_be_reused(self):
        provider = SequenceOTPProvider(['111111', '222222'])
        self.service.provider = provider
        first = self.service.send_otp(self.mobile)
        cache.set(
            self.service._get_rate_limit_key(self.mobile),
            timezone.now().timestamp() - 1,
            timeout=60,
        )
        second = self.service.send_otp(self.mobile)
        self.assertTrue(first['success'])
        self.assertTrue(second['success'])

        old_code = self.service.verify_otp(self.mobile, '111111')
        current_code = self.service.verify_otp(self.mobile, '222222')
        reused_code = self.service.verify_otp(self.mobile, '222222')

        self.assertFalse(old_code['success'])
        self.assertTrue(current_code['success'])
        self.assertFalse(reused_code['success'])
        self.assertEqual(provider.sent, [(self.mobile, '111111'), (self.mobile, '222222')])
        old_request = OTPRequest.objects.get(pk=first['otp_request_id'])
        current_request = OTPRequest.objects.get(pk=second['otp_request_id'])
        self.assertEqual(old_request.status, OTPRequest.STATUS_EXPIRED)
        self.assertEqual(current_request.status, OTPRequest.STATUS_VERIFIED)

    def test_malformed_otp_does_not_consume_attempts(self):
        self.service.send_otp(self.mobile)
        request = OTPRequest.objects.get(mobile_number=self.mobile)
        for value in ('12345', '1234567', 'abcdef', '12 345'):
            with self.subTest(value=value):
                result = self.service.verify_otp(self.mobile, value)
                self.assertFalse(result['success'])
        request.refresh_from_db()
        self.assertEqual(request.attempts, 0)
        self.assertEqual(request.status, OTPRequest.STATUS_PENDING)

    def test_phone_cooldown_is_shared_across_source_ips(self):
        first = self.service.send_otp(self.mobile, ip_address='192.0.2.10')
        second = self.service.send_otp(self.mobile, ip_address='192.0.2.11')
        self.assertTrue(first['success'])
        self.assertFalse(second['success'])
        self.assertGreater(second['cooldown_seconds'], 0)

    @override_settings(OTP_IP_REQUEST_LIMIT=1, OTP_IP_REQUEST_WINDOW_SECONDS=3600)
    def test_ip_rate_limit_counter_can_reset_for_a_new_window(self):
        self.service = OTPService()
        ip_address = '192.0.2.20'
        first = self.service.send_otp('+919876543210', ip_address=ip_address)
        blocked = self.service.send_otp('+919876543211', ip_address=ip_address)
        self.assertTrue(first['success'])
        self.assertFalse(blocked['success'])

        cache.delete(self.service._ip_request_key(ip_address))
        after_reset = self.service.send_otp('+919876543212', ip_address=ip_address)
        self.assertTrue(after_reset['success'])
