"""
Civic AI — Tests: Authentication, OTP Service & Providers
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from apps.accounts.models import User, OTPRequest
from apps.accounts.otp.service import OTPService
from apps.accounts.otp.providers import MockOTPProvider, get_otp_provider


class OTPServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.service = OTPService()
        self.mobile = '+919876543210'

    def test_mock_provider_configuration(self):
        provider = get_otp_provider()
        self.assertIsInstance(provider, MockOTPProvider)

    @override_settings(OTP_MOCK_ALLOWED=False)
    def test_mock_provider_fixed_code_is_disabled_outside_debug(self):
        provider = MockOTPProvider()
        self.assertFalse(provider.verify_otp('123456', provider.hash_otp('654321')))

    def test_mock_provider_cannot_be_selected_outside_debug(self):
        with override_settings(OTP_MOCK_ALLOWED=False, OTP_PROVIDER='mock'):
            with self.assertRaises(ImproperlyConfigured):
                get_otp_provider()

    @override_settings(OTP_MOCK_ALLOWED=True)
    def test_mock_provider_fixed_code_is_available_in_debug(self):
        provider = MockOTPProvider()
        self.assertTrue(provider.verify_otp('123456', provider.hash_otp('654321')))

    def test_send_otp_success(self):
        result = self.service.send_otp(self.mobile, purpose='login')
        self.assertTrue(result['success'])
        self.assertIn('cooldown_seconds', result)

        # Verify OTPRequest was created
        otp_req = OTPRequest.objects.filter(mobile_number=self.mobile).first()
        self.assertIsNotNone(otp_req)
        self.assertEqual(otp_req.status, OTPRequest.STATUS_PENDING)
        # Verify plaintext OTP is never saved
        self.assertNotEqual(otp_req.otp_hash, '123456')

    @override_settings(OTP_IP_REQUEST_LIMIT=1, OTP_IP_REQUEST_WINDOW_SECONDS=3600)
    def test_send_otp_is_limited_per_ip_across_phone_numbers(self):
        first = self.service.send_otp(self.mobile, purpose='login', ip_address='192.0.2.10')
        second = self.service.send_otp('+919876543211', purpose='login', ip_address='192.0.2.10')

        self.assertTrue(first['success'])
        self.assertFalse(second['success'])
        self.assertEqual(second['cooldown_seconds'], 3600)

    def test_verify_otp_with_mock_code(self):
        # Send OTP
        self.service.send_otp(self.mobile, purpose='login')

        # Verify with development mock code '123456'
        res = self.service.verify_otp(self.mobile, '123456')
        self.assertTrue(res['success'])
        self.assertTrue(res['is_new_user'])
        self.assertEqual(res['user'].mobile_number, self.mobile)

        # Status updated
        otp_req = OTPRequest.objects.filter(mobile_number=self.mobile).first()
        self.assertEqual(otp_req.status, OTPRequest.STATUS_VERIFIED)

    def test_verify_otp_invalid_code(self):
        self.service.send_otp(self.mobile, purpose='login')
        res = self.service.verify_otp(self.mobile, '000000')
        self.assertFalse(res['success'])
        self.assertIn('Invalid OTP', res['message'])


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.mobile = '9876543210'  # raw 10 digits

    def test_login_page_renders(self):
        resp = self.client.get(reverse('accounts:login'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Welcome Back')

    def test_fixed_otp_hint_is_only_rendered_for_allowed_development_mock(self):
        session = self.client.session
        session['pending_mobile'] = '+919876543210'
        session.save()

        with override_settings(DEBUG=True, OTP_MOCK_ALLOWED=True):
            development = self.client.get(reverse('accounts:verify_otp'), HTTP_HOST='localhost')
            self.assertContains(development, 'local mock OTP')
            self.assertContains(development, '123456')

        with override_settings(DEBUG=False, OTP_MOCK_ALLOWED=False):
            production = self.client.get(reverse('accounts:verify_otp'), HTTP_HOST='localhost')
            self.assertNotContains(production, 'local mock OTP')
            self.assertNotContains(production, '123456')

    def test_send_otp_post(self):
        resp = self.client.post(reverse('accounts:send_otp'), {'mobile_number': self.mobile}, follow=True)
        self.assertEqual(resp.status_code, 200)
        # Should redirect to verify_otp
        self.assertContains(resp, 'Verify OTP')
        self.assertIn('pending_mobile', self.client.session)

    def test_verify_otp_submit_new_user_redirects_to_setup(self):
        # Step 1: Send OTP
        self.client.post(reverse('accounts:send_otp'), {'mobile_number': self.mobile})

        # Step 2: Submit OTP 123456
        resp = self.client.post(
            reverse('accounts:verify_otp_submit'),
            {'otp_1': '1', 'otp_2': '2', 'otp_3': '3', 'otp_4': '4', 'otp_5': '5', 'otp_6': '6'},
            follow=False
        )
        # New user with incomplete profile redirects to profile setup
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/setup/', resp.url)

        # User is authenticated
        self.assertTrue(User.objects.filter(mobile_number='+919876543210').exists())
