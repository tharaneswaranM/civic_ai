"""
Civic AI — Optimizations and Resilience Tests
Covers schemes API resilience, applications tracker security, assistant robustness, and audit logging.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import translation
from django.contrib.auth import get_user_model
from apps.schemes.models import Scheme, SchemeVersion, SavedScheme, UserSchemeMatch
from apps.profiles.models import UserProfile
from apps.applications_tracker.models import ApplicationTracker
from apps.audit.models import AuditLog
from apps.audit.services import log_audit_event

User = get_user_model()


class OptimizationsAndResilienceTests(TestCase):
    def setUp(self):
        translation.activate('en')
        self.client = Client()
        self.user = User.objects.create_user(
            mobile_number='+919876543210',
            full_name='Aarav Sharma',
            preferred_language='en'
        )
        self.scheme = Scheme.objects.create(
            name='Test Kisan Scheme',
            slug='test-kisan-scheme',
            level=Scheme.LEVEL_CENTRAL,
            status=Scheme.STATUS_ACTIVE
        )
        self.version = SchemeVersion.objects.create(
            scheme=self.scheme,
            version_number=1,
            description='Test scheme for farmers',
            benefit_summary='Rs 6000 annual subsidy',
            review_status=SchemeVersion.REVIEW_APPROVED
        )
        self.scheme.current_version = self.version
        self.scheme.save()

    def test_scheme_detail_view_anonymous_and_authenticated(self):
        # Anonymous
        resp = self.client.get(reverse('schemes:detail', kwargs={'slug': self.scheme.slug}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Test Kisan Scheme')

        # Authenticated
        self.client.force_login(self.user)
        resp_auth = self.client.get(reverse('schemes:detail', kwargs={'slug': self.scheme.slug}))
        self.assertEqual(resp_auth.status_code, 200)

    def test_save_scheme_records_audit_log(self):
        self.client.force_login(self.user)
        url = reverse('schemes:save', kwargs={'slug': self.scheme.slug})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(SavedScheme.objects.filter(user=self.user, scheme=self.scheme).exists())

        # Check audit log recorded
        audit = AuditLog.objects.filter(user=self.user, event=AuditLog.EVENT_SCHEME_SAVED).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.metadata.get('scheme_id'), str(self.scheme.id))

        # The desired action is explicit, so duplicate saves stay idempotent.
        duplicate_save = self.client.post(url, {'action': 'save'})
        self.assertEqual(duplicate_save.status_code, 302)
        self.assertEqual(
            SavedScheme.objects.filter(user=self.user, scheme=self.scheme).count(), 1
        )

        # Removal is explicit rather than an implicit toggle.
        resp2 = self.client.post(url, {'action': 'remove'})
        self.assertEqual(resp2.status_code, 302)
        self.assertFalse(SavedScheme.objects.filter(user=self.user, scheme=self.scheme).exists())

    def test_scheme_detail_api_invalid_uuid(self):
        resp = self.client.get('/api/schemes/not-a-valid-uuid/')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json(), {'error': 'Not found'})

    def test_scheme_eligibility_api_missing_profile(self):
        user_no_profile = User.objects.create_user(mobile_number='+919876543299')
        self.client.force_login(user_no_profile)
        resp = self.client.get(f'/api/schemes/{self.scheme.id}/eligibility/')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('User profile not found', resp.json().get('error', ''))

    def test_scheme_eligibility_api_invalid_uuid(self):
        self.client.force_login(self.user)
        resp = self.client.get('/api/schemes/invalid-uuid/eligibility/')
        self.assertEqual(resp.status_code, 404)

    def test_scheme_eligibility_api_success(self):
        UserProfile.objects.create(user=self.user, age=30)
        self.client.force_login(self.user)
        resp = self.client.get(f'/api/schemes/{self.scheme.id}/eligibility/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('result', resp.json())

    def test_applications_tracker_update_status_require_post(self):
        self.client.force_login(self.user)
        app = ApplicationTracker.objects.create(user=self.user, scheme=self.scheme)
        url = reverse('applications:update_status', kwargs={'pk': app.pk})

        # GET should be rejected with 405 Method Not Allowed
        resp_get = self.client.get(url)
        self.assertEqual(resp_get.status_code, 405)

        # POST should succeed
        resp_post = self.client.post(url, {'status': ApplicationTracker.STATUS_SUBMITTED})
        self.assertEqual(resp_post.status_code, 302)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationTracker.STATUS_SUBMITTED)
        audit = AuditLog.objects.filter(
            user=self.user, event=AuditLog.EVENT_APPLICATION_STATUS_CHANGED
        ).latest('created_at')
        self.assertEqual(audit.metadata['application_id'], str(app.pk))
        self.assertEqual(audit.metadata['new_status'], ApplicationTracker.STATUS_SUBMITTED)

    def test_application_creation_requires_post(self):
        self.client.force_login(self.user)
        url = reverse('applications:add', kwargs={'scheme_slug': self.scheme.slug})

        get_response = self.client.get(url)

        self.assertEqual(get_response.status_code, 405)
        self.assertFalse(ApplicationTracker.objects.filter(user=self.user, scheme=self.scheme).exists())

        post_response = self.client.post(url)

        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(ApplicationTracker.objects.filter(user=self.user, scheme=self.scheme).exists())

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        url = reverse('accounts:logout')

        get_response = self.client.get(url)

        self.assertEqual(get_response.status_code, 405)
        self.assertTrue(self.client.session.get('_auth_user_id'))

        post_response = self.client.post(url)

        self.assertEqual(post_response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertTrue(AuditLog.objects.filter(
            user=self.user, event=AuditLog.EVENT_LOGOUT
        ).exists())

    def test_assistant_chat_api_invalid_conversation_id(self):
        self.client.force_login(self.user)
        # Pass a bogus string as conversation_id
        resp = self.client.post(
            '/api/assistant/chat/',
            {'message': 'What schemes am I eligible for?', 'conversation_id': 'bogus-id-123'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertIn('conversation_id', data)

    def test_audit_services_logging(self):
        log = log_audit_event(
            event=AuditLog.EVENT_LOGIN_SUCCESS,
            user=self.user,
            mobile_masked='******3210',
            metadata={'source': 'test'}
        )
        self.assertIsNotNone(log)
        self.assertEqual(log.event, AuditLog.EVENT_LOGIN_SUCCESS)
        self.assertEqual(log.mobile_masked, '******3210')
        self.assertEqual(log.metadata, {'source': 'test'})
