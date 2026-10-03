"""Regression tests for per-user data ownership and browser CSRF protection."""
import json

from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.applications_tracker.models import ApplicationTracker
from apps.assistant.models import AssistantConversation, AssistantMessage
from apps.documents.models import DocumentChecklist
from apps.notifications.models import Notification
from apps.profiles.models import UserProfile
from apps.schemes.models import SavedScheme, Scheme, SchemeVersion, UserSchemeMatch


class UserDataOwnershipTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            mobile_number='+919876543210', full_name='Citizen A', preferred_language='en'
        )
        self.user_b = User.objects.create_user(
            mobile_number='+919876543211', full_name='Citizen B', preferred_language='en'
        )
        self.scheme = Scheme.objects.create(
            name='Shared Scheme', slug='shared-scheme', level=Scheme.LEVEL_CENTRAL,
            status=Scheme.STATUS_ACTIVE,
        )
        self.version = SchemeVersion.objects.create(
            scheme=self.scheme, version_number=1, description='Public scheme description',
            benefit_summary='Public benefit', review_status=SchemeVersion.REVIEW_APPROVED,
        )
        self.scheme.current_version = self.version
        self.scheme.save(update_fields=['current_version'])
        self.application_b = ApplicationTracker.objects.create(
            user=self.user_b, scheme=self.scheme, status=ApplicationTracker.STATUS_SUBMITTED,
            notes='Private application note',
        )
        self.notification_b = Notification.objects.create(
            user=self.user_b, notification_type=Notification.TYPE_GENERAL,
            title='Private notification title', body='Private notification body',
        )
        self.saved_b = SavedScheme.objects.create(user=self.user_b, scheme=self.scheme)
        self.document_b = DocumentChecklist.objects.create(
            user=self.user_b, scheme=self.scheme, document_name='Private income proof',
        )
        self.profile_b = UserProfile.objects.create(user=self.user_b, city_village='Private Village')
        UserSchemeMatch.objects.create(
            user=self.user_b, scheme=self.scheme, scheme_version=self.version,
            result=UserSchemeMatch.RESULT_ELIGIBLE, matched_rules=[], missing_info=[],
        )
        self.conversation_b = AssistantConversation.objects.create(
            user=self.user_b, title='Private conversation', language='en',
        )
        self.message_b = AssistantMessage.objects.create(
            conversation=self.conversation_b, role=AssistantMessage.ROLE_USER,
            content='Private assistant message',
        )
        self.client = Client()
        self.client.force_login(self.user_a)

    def test_user_a_cannot_read_or_modify_user_b_application(self):
        response = self.client.get(reverse('applications:detail', args=[self.application_b.pk]))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse('applications:update_status', args=[self.application_b.pk]),
            {'status': ApplicationTracker.STATUS_APPROVED},
        )
        self.assertEqual(response.status_code, 404)
        self.application_b.refresh_from_db()
        self.assertEqual(self.application_b.status, ApplicationTracker.STATUS_SUBMITTED)
        self.assertEqual(self.application_b.notes, 'Private application note')

    def test_user_a_cannot_read_or_mark_user_b_notification(self):
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Private notification title')
        self.assertNotContains(response, 'Private notification body')

        response = self.client.get(reverse('api_notifications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Private notification title', response.content.decode())

        response = self.client.post(reverse('notifications:mark_read', args=[self.notification_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.notification_b.refresh_from_db()
        self.assertFalse(self.notification_b.is_read)

    def test_user_a_cannot_read_or_change_user_b_saved_scheme_or_match(self):
        response = self.client.get(reverse('schemes:detail', kwargs={'slug': self.scheme.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['scheme'].is_saved_by_user)
        self.assertIsNone(response.context['eligibility_result'])

        response = self.client.get(reverse('api_schemes:recommended'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['recommended'], [])

        save_url = reverse('schemes:save', kwargs={'slug': self.scheme.slug})
        self.assertEqual(self.client.post(save_url, {'action': 'save'}).status_code, 302)
        self.assertTrue(SavedScheme.objects.filter(user=self.user_a, scheme=self.scheme).exists())
        self.assertTrue(SavedScheme.objects.filter(pk=self.saved_b.pk, user=self.user_b).exists())

        self.assertEqual(self.client.post(save_url, {'action': 'remove'}).status_code, 302)
        self.assertFalse(SavedScheme.objects.filter(user=self.user_a, scheme=self.scheme).exists())
        self.assertTrue(SavedScheme.objects.filter(pk=self.saved_b.pk, user=self.user_b).exists())

    def test_user_a_cannot_read_user_b_document_checklist(self):
        response = self.client.get(reverse('documents:overview'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Private income proof')
        self.assertNotIn(self.document_b, response.context['checklist'])

    def test_user_a_cannot_reuse_user_b_assistant_conversation(self):
        before_count = self.conversation_b.messages.count()
        response = self.client.post(
            reverse('api_assistant:chat'),
            data=json.dumps({
                'message': 'Show my scheme guidance',
                'conversation_id': str(self.conversation_b.pk),
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotEqual(data['conversation_id'], str(self.conversation_b.pk))
        self.assertEqual(self.conversation_b.messages.count(), before_count)
        self.assertTrue(
            AssistantConversation.objects.filter(pk=data['conversation_id'], user=self.user_a).exists()
        )
        self.assertFalse(
            AssistantMessage.objects.filter(
                conversation__user=self.user_a, content='Private assistant message'
            ).exists()
        )

    def test_profile_updates_are_bound_to_authenticated_user(self):
        response = self.client.get(reverse('dashboard:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile'].user_id, self.user_a.pk)

        response = self.client.post(
            reverse('dashboard:profile_setup_step', args=[1]),
            {'user_id': str(self.user_b.pk), 'full_name': 'Updated Citizen A',
             'gender': 'female', 'preferred_language': 'en'},
        )
        self.assertEqual(response.status_code, 302)
        self.user_a.refresh_from_db()
        self.user_b.refresh_from_db()
        self.profile_b.refresh_from_db()
        self.assertEqual(self.user_a.full_name, 'Updated Citizen A')
        self.assertEqual(self.user_b.full_name, 'Citizen B')
        self.assertEqual(self.profile_b.city_village, 'Private Village')


class BrowserCSRFSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(mobile_number='+919876543210')
        self.scheme = Scheme.objects.create(
            name='CSRF Test Scheme', slug='csrf-test-scheme', level=Scheme.LEVEL_CENTRAL,
            status=Scheme.STATUS_ACTIVE,
        )
        self.application = ApplicationTracker.objects.create(user=self.user, scheme=self.scheme)
        self.notification = Notification.objects.create(
            user=self.user, notification_type=Notification.TYPE_GENERAL,
            title='CSRF notification', body='Test body',
        )
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.user)

    def test_browser_state_changes_reject_missing_csrf_token(self):
        requests = [
            ('logout', reverse('accounts:logout'), {}),
            ('send OTP', reverse('accounts:send_otp'), {'mobile_number': '9876543210'}),
            ('verify OTP', reverse('accounts:verify_otp_submit'), {'otp': '123456'}),
            ('profile update', reverse('dashboard:profile_setup_step', args=[1]), {'full_name': 'No CSRF'}),
            ('save scheme', reverse('schemes:save', kwargs={'slug': self.scheme.slug}), {'action': 'save'}),
            ('remove scheme', reverse('schemes:save', kwargs={'slug': self.scheme.slug}), {'action': 'remove'}),
            ('create application', reverse('applications:add', kwargs={'scheme_slug': self.scheme.slug}), {}),
            ('update application', reverse('applications:update_status', args=[self.application.pk]),
             {'status': ApplicationTracker.STATUS_SUBMITTED}),
            ('mark notification read', reverse('notifications:mark_read', args=[self.notification.pk]), {}),
            ('mark all notifications read', reverse('notifications:mark_all_read'), {}),
        ]
        for label, url, data in requests:
            with self.subTest(action=label):
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, 403)
