"""Query bounds and pagination regression tests for growing per-user lists."""
import json

from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext

from apps.accounts.models import User
from apps.applications_tracker.models import ApplicationTracker
from apps.documents.models import DocumentChecklist
from apps.notifications.models import Notification
from apps.schemes.models import Scheme


class BoundedUserListsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(mobile_number='+919876543210')
        self.client = Client()
        self.client.force_login(self.user)
        self.schemes = [
            Scheme.objects.create(
                name=f'Query Scheme {index:02}', slug=f'query-scheme-{index:02}',
                level=Scheme.LEVEL_CENTRAL, status=Scheme.STATUS_ACTIVE,
            )
            for index in range(30)
        ]
        for scheme in self.schemes:
            ApplicationTracker.objects.create(user=self.user, scheme=scheme)
            DocumentChecklist.objects.create(
                user=self.user, scheme=scheme, document_name=f'Document for {scheme.slug}',
            )
        for index in range(30):
            Notification.objects.create(
                user=self.user, notification_type=Notification.TYPE_GENERAL,
                title=f'Notification {index:02}', body='A bounded test notification.',
            )

    def _get_with_query_bound(self, url):
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(captured), 12, f'{url} ran {len(captured)} queries')
        return response

    def test_application_list_is_paginated_and_has_bounded_query_count(self):
        first = self._get_with_query_bound('/applications/')
        self.assertEqual(len(first.context['applications']), 25)
        self.assertEqual(first.context['applications'].paginator.count, 30)
        self.assertTrue(first.context['applications'].has_next())

        second = self._get_with_query_bound('/applications/?page=2')
        self.assertEqual(len(second.context['applications']), 5)
        self.assertFalse(second.context['applications'].has_next())

    def test_document_checklist_is_paginated_and_has_bounded_query_count(self):
        first = self._get_with_query_bound('/documents/')
        self.assertEqual(len(first.context['checklist']), 25)
        self.assertEqual(first.context['checklist'].paginator.count, 30)
        self.assertTrue(first.context['checklist'].has_next())

        second = self._get_with_query_bound('/documents/?page=2')
        self.assertEqual(len(second.context['checklist']), 5)
        self.assertFalse(second.context['checklist'].has_next())

    def test_dashboard_scheme_notification_profile_and_assistant_queries_are_bounded(self):
        responses = [
            self._get_with_query_bound('/dashboard/'),
            self._get_with_query_bound('/schemes/'),
            self._get_with_query_bound(f'/schemes/{self.schemes[0].slug}/'),
            self._get_with_query_bound('/notifications/'),
            self._get_with_query_bound('/dashboard/profile/'),
        ]
        self.assertTrue(all(response.status_code == 200 for response in responses))

        with CaptureQueriesContext(connection) as captured:
            response = self.client.post(
                '/api/assistant/chat/',
                data=json.dumps({'message': 'What documents do I need?'}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(captured), 12, f'assistant API ran {len(captured)} queries')
