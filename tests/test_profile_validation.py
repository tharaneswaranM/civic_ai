"""Regression coverage for server-side profile wizard validation."""
from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.profiles.models import UserProfile
from apps.states.models import District, State


class ProfileWizardValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(mobile_number='+919876543210')
        self.client.force_login(self.user)
        self.ap = State.objects.create(
            code='AP', name='Andhra Pradesh', native_name='ఆంధ్ర ప్రదేశ్', slug='andhra-pradesh'
        )
        self.tn = State.objects.create(
            code='TN', name='Tamil Nadu', native_name='தமிழ் நாடு', slug='tamil-nadu'
        )
        self.tn_district = District.objects.create(state=self.tn, name='Chennai')

    def test_future_date_of_birth_is_rejected_without_saving_profile(self):
        future_date = (date.today() + timedelta(days=1)).isoformat()

        response = self.client.post(reverse('dashboard:profile_setup_step', args=[1]), {
            'full_name': 'Test Citizen',
            'date_of_birth': future_date,
            'gender': 'female',
            'preferred_language': 'en',
        })

        self.assertEqual(response.status_code, 200)
        profile = UserProfile.objects.get(user=self.user)
        self.assertIsNone(profile.date_of_birth)
        self.assertEqual(profile.gender, '')
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, '')

    def test_district_from_another_state_is_rejected(self):
        response = self.client.post(reverse('dashboard:profile_setup_step', args=[2]), {
            'state': str(self.ap.pk),
            'district': str(self.tn_district.pk),
            'pin_code': '600001',
            'is_rural': 'false',
        })

        self.assertEqual(response.status_code, 200)
        profile = UserProfile.objects.get(user=self.user)
        self.assertIsNone(profile.state)
        self.assertIsNone(profile.district)

    def test_invalid_choice_is_rejected(self):
        response = self.client.post(reverse('dashboard:profile_setup_step', args=[3]), {
            'education_level': 'invented-level',
            'employment_status': 'employed',
            'occupation': 'Teacher',
            'sector': 'Education',
            'is_student': 'false',
        })

        self.assertEqual(response.status_code, 200)
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.education_level, '')
        self.assertEqual(profile.employment_status, '')

    def test_out_of_range_step_redirects_to_first_step(self):
        response = self.client.get(reverse('dashboard:profile_setup_step', args=[6]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:profile_setup_step', args=[1]))

    def test_malformed_and_wrong_length_pin_codes_are_not_saved(self):
        for pin in ('12A456', '12345', '1234567'):
            with self.subTest(pin=pin):
                response = self.client.post(reverse('dashboard:profile_setup_step', args=[2]), {
                    'state': str(self.ap.pk), 'pin_code': pin, 'is_rural': 'false',
                })
                self.assertEqual(response.status_code, 200)
                profile = UserProfile.objects.get(user=self.user)
                self.assertIsNone(profile.state)
                self.assertEqual(profile.pin_code, '')

    def test_invalid_boolean_values_are_not_saved(self):
        response = self.client.post(reverse('dashboard:profile_setup_step', args=[2]), {
            'state': str(self.ap.pk), 'pin_code': '600001', 'is_rural': 'perhaps',
        })
        self.assertEqual(response.status_code, 200)
        profile = UserProfile.objects.get(user=self.user)
        self.assertIsNone(profile.state)
        self.assertEqual(profile.pin_code, '')

        response = self.client.post(reverse('dashboard:profile_setup_step', args=[5]), {
            'is_farmer': 'yes-ish', 'land_holding': 'small',
        })
        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertIsNone(profile.is_farmer)
        self.assertEqual(profile.land_holding, '')

    def test_negative_and_unreasonably_high_dependents_are_not_saved(self):
        for count in ('-1', '101'):
            with self.subTest(count=count):
                response = self.client.post(reverse('dashboard:profile_setup_step', args=[4]), {
                    'number_of_dependents': count, 'category': 'sc',
                })
                self.assertEqual(response.status_code, 200)
                profile = UserProfile.objects.get(user=self.user)
                self.assertIsNone(profile.number_of_dependents)
                self.assertEqual(profile.category, '')

    def test_invalid_social_category_is_not_saved(self):
        response = self.client.post(reverse('dashboard:profile_setup_step', args=[4]), {
            'number_of_dependents': '2', 'category': 'invented-category',
        })
        self.assertEqual(response.status_code, 200)
        profile = UserProfile.objects.get(user=self.user)
        self.assertIsNone(profile.number_of_dependents)
        self.assertEqual(profile.category, '')

    def test_farmer_false_clears_stale_landholding_and_valid_landholding_is_accepted(self):
        profile = UserProfile.objects.create(user=self.user)
        profile.land_holding = UserProfile.LAND_LARGE
        profile.save(update_fields=['land_holding'])

        response = self.client.post(reverse('dashboard:profile_setup_step', args=[5]), {
            'is_farmer': 'false', 'land_holding': UserProfile.LAND_LARGE,
        })
        self.assertEqual(response.status_code, 302)
        profile.refresh_from_db()
        self.assertFalse(profile.is_farmer)
        self.assertEqual(profile.land_holding, '')
        audit = AuditLog.objects.filter(
            user=self.user, event=AuditLog.EVENT_PROFILE_UPDATED
        ).latest('created_at')
        self.assertEqual(audit.metadata, {'profile_step': 5})

        response = self.client.post(reverse('dashboard:profile_setup_step', args=[5]), {
            'is_farmer': 'true', 'land_holding': UserProfile.LAND_MARGINAL,
        })
        self.assertEqual(response.status_code, 302)
        profile.refresh_from_db()
        self.assertTrue(profile.is_farmer)
        self.assertEqual(profile.land_holding, UserProfile.LAND_MARGINAL)

    def test_invalid_landholding_choice_is_not_saved(self):
        response = self.client.post(reverse('dashboard:profile_setup_step', args=[5]), {
            'is_farmer': 'true', 'land_holding': 'invented-size',
        })
        self.assertEqual(response.status_code, 200)
        profile = UserProfile.objects.get(user=self.user)
        self.assertIsNone(profile.is_farmer)
        self.assertEqual(profile.land_holding, '')

    def test_student_false_clears_student_only_course(self):
        profile = UserProfile.objects.create(user=self.user)
        profile.student_course = 'Old course value'
        profile.is_student = True
        profile.save(update_fields=['student_course', 'is_student'])

        response = self.client.post(reverse('dashboard:profile_setup_step', args=[3]), {
            'is_student': 'false', 'student_course': 'Submitted stale value',
            'education_level': UserProfile.EDUCATION_GRADUATE,
            'employment_status': UserProfile.EMPLOYMENT_EMPLOYED,
        })
        self.assertEqual(response.status_code, 302)
        profile.refresh_from_db()
        self.assertFalse(profile.is_student)
        self.assertEqual(profile.student_course, '')

    def test_unreasonably_old_dob_is_rejected_without_saving(self):
        old_date = date.today().replace(year=date.today().year - 121).isoformat()
        response = self.client.post(reverse('dashboard:profile_setup_step', args=[1]), {
            'full_name': 'Test Citizen', 'date_of_birth': old_date,
            'gender': 'female', 'preferred_language': 'en',
        })
        self.assertEqual(response.status_code, 200)
        profile = UserProfile.objects.get(user=self.user)
        self.assertIsNone(profile.date_of_birth)
        self.assertIsNone(profile.age)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, '')
