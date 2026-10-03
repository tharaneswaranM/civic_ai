"""Tests for URL safety, redirect handling, and POST-only state changes."""
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import translation

from apps.accounts.models import User
from apps.applications_tracker.models import ApplicationTracker
from apps.notifications.models import Notification
from apps.security import safe_action_url, safe_external_https_url
from apps.schemes.models import Scheme


class ExternalURLValidationTests(TestCase):
    def setUp(self):
        translation.activate('en')
        self.request = RequestFactory().get('/')

    def test_external_scheme_url_accepts_https_and_rejects_unsafe_forms(self):
        self.assertEqual(
            safe_external_https_url('https://portal.example.gov/apply'),
            'https://portal.example.gov/apply',
        )
        for value in (
            'http://portal.example.gov/apply', 'javascript:alert(1)',
            'data:text/html,hello', 'file:///etc/passwd',
            '//evil.example/path', 'https://user:pass@example.gov/',
            ' https://example.gov/', 'https://example.gov:bad/',
        ):
            with self.subTest(value=value):
                self.assertEqual(safe_external_https_url(value), '')

    def test_notification_action_url_allows_local_path_and_safe_https_only(self):
        self.assertEqual(safe_action_url('/dashboard/', self.request), '/dashboard/')
        self.assertEqual(
            safe_action_url('https://portal.example.gov/apply', self.request),
            'https://portal.example.gov/apply',
        )
        for value in (
            '//evil.example/path', 'javascript:alert(1)', 'data:text/html,hello',
            'file:///tmp/secret', 'http://portal.example.gov/', '/\\evil.example/path',
        ):
            with self.subTest(value=value):
                self.assertEqual(safe_action_url(value, self.request), '')

    def test_language_redirect_rejects_external_and_protocol_relative_destinations(self):
        client = Client()
        for target in ('https://evil.example/', '//evil.example/path'):
            with self.subTest(target=target):
                response = client.post(reverse('states:set_language'), {
                    'language_code': 'te', 'next': target,
                })
                self.assertEqual(response.status_code, 302)
                self.assertNotIn('evil.example', response['Location'])
                self.assertEqual(response['Location'], '/te/auth/login/')

    def test_language_redirect_keeps_each_safe_app_destination(self):
        for destination in (
            '/dashboard/', '/schemes/', '/applications/', '/documents/',
            '/notifications/', '/assistant/',
        ):
            with self.subTest(destination=destination):
                response = Client().post(reverse('states:set_language'), {
                    'language_code': 'te', 'next': destination,
                })
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response['Location'], destination)
                self.assertEqual(response.cookies['django_language'].value, 'te')


class StateChangingHTTPMethodTests(TestCase):
    def setUp(self):
        translation.activate('en')
        self.user = User.objects.create_user(mobile_number='+919876543210')
        self.scheme = Scheme.objects.create(
            name='Method Test Scheme', slug='method-test-scheme',
            level=Scheme.LEVEL_CENTRAL, status=Scheme.STATUS_ACTIVE,
        )
        self.application = ApplicationTracker.objects.create(user=self.user, scheme=self.scheme)
        self.notification = Notification.objects.create(
            user=self.user, notification_type=Notification.TYPE_GENERAL,
            title='Method test', body='Test body',
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_all_browser_mutation_routes_reject_get(self):
        routes = [
            ('set state', reverse('states:set_state')),
            ('set language', reverse('states:set_language')),
            ('send OTP', reverse('accounts:send_otp')),
            ('verify OTP', reverse('accounts:verify_otp_submit')),
            ('resend OTP', reverse('accounts:resend_otp')),
            ('logout', reverse('accounts:logout')),
            ('save scheme', reverse('schemes:save', kwargs={'slug': self.scheme.slug})),
            ('update application', reverse('applications:update_status', args=[self.application.pk])),
            ('add application', reverse('applications:add', kwargs={'scheme_slug': self.scheme.slug})),
            ('mark notification read', reverse('notifications:mark_read', args=[self.notification.pk])),
            ('mark all notifications read', reverse('notifications:mark_all_read')),
        ]
        for label, url in routes:
            with self.subTest(action=label):
                self.assertEqual(self.client.get(url).status_code, 405)
