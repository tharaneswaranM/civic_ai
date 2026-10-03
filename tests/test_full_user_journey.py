"""
Civic AI — End-to-End User Journey Integration Test
Verifies the complete flow from Landing to State Selection, Language Selection,
Mobile OTP Login, 5-Step Profile Setup, Eligibility Matching, Dashboard,
Scheme Discovery, Application Tracking, and AI Assistant.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import translation
from django.core.cache import cache
from apps.states.models import State, District, Language
from apps.schemes.models import (
    Scheme, SchemeVersion, EligibilityRule, RequiredDocument,
    SchemeCategory, UserSchemeMatch, SavedScheme
)
from apps.applications_tracker.models import ApplicationTracker
from apps.notifications.models import Notification
from apps.accounts.models import User


class FullUserJourneyTest(TestCase):
    def setUp(self):
        translation.activate('en')
        cache.clear()
        self.client = Client()

        # 1. Setup Languages
        self.en = Language.objects.create(code='en', name='English', native_name='English', display_order=1)
        self.te = Language.objects.create(code='te', name='Telugu', native_name='తెలుగు', display_order=2)
        self.ta = Language.objects.create(code='ta', name='Tamil', native_name='தமிழ்', display_order=3)

        # 2. Setup States
        self.ap = State.objects.create(
            code='AP',
            name='Andhra Pradesh',
            native_name='ఆంధ్ర ప్రదేశ్',
            slug='andhra-pradesh',
            transition_title='Welcome to Andhra Pradesh',
            transition_subtitle='Personalized schemes for you.',
            transition_color_primary='#003580',
            transition_landmark='Tirumala Venkateswara Temple',
            display_order=1,
            is_active=True,
        )
        self.ap.languages.set([self.en, self.te])

        self.district_vizag = District.objects.create(state=self.ap, name='Visakhapatnam', is_active=True)

        # 3. Setup Categories & Schemes
        self.cat_farm = SchemeCategory.objects.create(name='Agriculture & Farmers', slug='agriculture-farmers')

        self.scheme_ap = Scheme.objects.create(
            name='YSR Rythu Bharosa',
            slug='ysr-rythu-bharosa',
            level='state',
            state=self.ap,
            status=Scheme.STATUS_ACTIVE,
            is_new=True,
            official_url='https://apagrisnet.gov.in/',
        )
        self.scheme_ap.categories.add(self.cat_farm)

        self.version_ap = SchemeVersion.objects.create(
            scheme=self.scheme_ap,
            version_number=1,
            description='Financial assistance for Andhra Pradesh agricultural farmers.',
            benefit_summary='Rs 13,500 per year per farmer family.',
            how_to_apply='Apply online via village secretariat or MeeSeva.',
            review_status='approved',
        )
        self.scheme_ap.current_version = self.version_ap
        self.scheme_ap.save()

        # Rules: Resident of AP, Must be Farmer, Individual Income <= 500000
        EligibilityRule.objects.create(
            scheme_version=self.version_ap,
            rule_type=EligibilityRule.RULE_STATE,
            value='AP',
            is_mandatory=True,
            display_label='Andhra Pradesh Resident',
        )
        EligibilityRule.objects.create(
            scheme_version=self.version_ap,
            rule_type=EligibilityRule.RULE_IS_FARMER,
            value='true',
            is_mandatory=True,
            display_label='Must be a Farmer',
        )
        EligibilityRule.objects.create(
            scheme_version=self.version_ap,
            rule_type=EligibilityRule.RULE_MAX_INDIVIDUAL_INCOME,
            value='500000',
            is_mandatory=True,
            display_label='Income below Rs 5 Lakhs',
        )

        RequiredDocument.objects.create(
            scheme_version=self.version_ap,
            name='Pattadar Passbook',
            is_mandatory=True,
        )

    def test_complete_citizen_onboarding_and_scheme_journey(self):
        # ── Step 1: Visit Landing Page ──
        resp_landing = self.client.get(reverse('states:landing'))
        self.assertEqual(resp_landing.status_code, 200)
        self.assertContains(resp_landing, 'Civic AI')
        self.assertContains(resp_landing, 'Andhra Pradesh')

        # ── Step 2: Choose State (Andhra Pradesh) ──
        resp_state = self.client.post(
            reverse('states:set_state'),
            {'state_slug': 'andhra-pradesh'},
            follow=True
        )
        self.assertEqual(resp_state.status_code, 200)
        self.assertEqual(resp_state.wsgi_request.LANGUAGE_CODE, 'te')
        self.assertContains(resp_state, 'ఆంధ్రప్రదేశ్‌కు స్వాగతం')
        self.assertEqual(self.client.session.get('selected_state'), 'andhra-pradesh')

        # ── Step 3: Choose Language (Telugu) ──
        resp_lang = self.client.post(
            reverse('states:set_language'),
            {'language_code': 'te'},
            follow=True
        )
        self.assertEqual(resp_lang.status_code, 200)
        self.assertEqual(self.client.session.get('selected_language'), 'te')

        # ── Step 4: Login with Mobile Number ──
        resp_send_otp = self.client.post(
            reverse('accounts:send_otp'),
            {'mobile_number': '9876543210'},
            follow=True
        )
        self.assertEqual(resp_send_otp.status_code, 200)
        self.assertEqual(resp_send_otp.wsgi_request.LANGUAGE_CODE, 'te')
        self.assertContains(resp_send_otp, '******3210')

        # ── Step 5: Verify OTP ──
        resp_verify = self.client.post(
            reverse('accounts:verify_otp_submit'),
            {'otp_1': '1', 'otp_2': '2', 'otp_3': '3', 'otp_4': '4', 'otp_5': '5', 'otp_6': '6'},
            follow=True
        )
        self.assertEqual(resp_verify.status_code, 200)
        # Should now be on profile setup step 1
        self.assertEqual(resp_verify.wsgi_request.LANGUAGE_CODE, 'te')
        self.assertContains(resp_verify, 'వ్యక్తిగత సమాచారం')

        # Verify user is authenticated
        user = User.objects.get(mobile_number='+919876543210')
        self.assertEqual(user.preferred_state, self.ap)
        self.assertEqual(user.preferred_language, 'te')

        # ── Step 6: Profile Setup Wizard (Steps 1 to 5) ──
        # Step 1: Personal Info
        resp_s1 = self.client.post(
            reverse('dashboard:profile_setup_step', kwargs={'step': 1}),
            {
                'full_name': 'K. Venkat Rao',
                'date_of_birth': '1995-05-15',
                'gender': 'male',
                'preferred_language': 'te',
            },
            follow=True
        )
        self.assertEqual(resp_s1.status_code, 200)
        self.assertContains(resp_s1, 'ప్రాంతం')

        # Step 2: Location
        resp_s2 = self.client.post(
            reverse('dashboard:profile_setup_step', kwargs={'step': 2}),
            {
                'state': str(self.ap.id),
                'district': str(self.district_vizag.id),
                'city_village': 'Anakapalle',
                'pin_code': '531001',
                'is_rural': 'true',
            },
            follow=True
        )
        self.assertEqual(resp_s2.status_code, 200)
        self.assertContains(resp_s2, 'విద్య మరియు ఉపాధి')

        # Step 3: Education & Employment
        resp_s3 = self.client.post(
            reverse('dashboard:profile_setup_step', kwargs={'step': 3}),
            {
                'education_level': 'graduate',
                'employment_status': 'farmer',
                'occupation': 'Agriculture',
                'sector': 'Farming',
                'is_student': 'false',
            },
            follow=True
        )
        self.assertEqual(resp_s3.status_code, 200)
        self.assertContains(resp_s3, 'ఆదాయం మరియు కుటుంబం')

        # Step 4: Income & Category
        resp_s4 = self.client.post(
            reverse('dashboard:profile_setup_step', kwargs={'step': 4}),
            {
                'individual_income_range': '1l_2_5l',
                'family_income_range': '2_5l_5l',
                'marital_status': 'married',
                'number_of_dependents': '3',
                'category': 'obc',
            },
            follow=True
        )
        self.assertEqual(resp_s4.status_code, 200)
        self.assertContains(resp_s4, 'అదనపు వివరాలు')

        # Step 5: Scheme Attributes (Farmer, Land holding)
        resp_s5 = self.client.post(
            reverse('dashboard:profile_setup_step', kwargs={'step': 5}),
            {
                'is_farmer': 'true',
                'land_holding': 'small',
                'has_disability': 'false',
                'is_senior_citizen': 'false',
                'is_widow': 'false',
                'is_shg_member': 'false',
                'is_job_seeker': 'false',
                'is_entrepreneur': 'false',
                'is_ration_card_holder': 'true',
            },
            follow=True
        )
        self.assertEqual(resp_s5.status_code, 200)
        # Should now be on the Dashboard!
        self.assertContains(resp_s5, 'డ్యాష్‌బోర్డ్')
        self.assertContains(resp_s5, 'మీ కోసం సూచించినవి')
        self.assertContains(resp_s5, 'YSR Rythu Bharosa')

        # Verify eligibility match created
        match = UserSchemeMatch.objects.filter(user=user, scheme=self.scheme_ap).first()
        self.assertIsNotNone(match)
        self.assertEqual(match.result, UserSchemeMatch.RESULT_ELIGIBLE)

        # ── Step 7: Explore Schemes Page ──
        resp_schemes = self.client.get(reverse('schemes:list'))
        self.assertEqual(resp_schemes.status_code, 200)
        self.assertContains(resp_schemes, 'YSR Rythu Bharosa')

        # Filter by eligible only
        resp_my_schemes = self.client.get(reverse('schemes:list') + '?eligible=1')
        self.assertEqual(resp_my_schemes.status_code, 200)
        self.assertContains(resp_my_schemes, 'YSR Rythu Bharosa')

        # ── Step 8: View Scheme Detail Page ──
        resp_detail = self.client.get(reverse('schemes:detail', kwargs={'slug': self.scheme_ap.slug}))
        self.assertEqual(resp_detail.status_code, 200)
        self.assertContains(resp_detail, 'YSR Rythu Bharosa')
        self.assertContains(resp_detail, 'మీరు అర్హులై ఉండవచ్చు!')
        self.assertContains(resp_detail, 'Pattadar Passbook')

        # ── Step 9: Save Scheme ──
        resp_save = self.client.post(reverse('schemes:save', kwargs={'slug': self.scheme_ap.slug}), follow=True)
        self.assertEqual(resp_save.status_code, 200)
        self.assertTrue(SavedScheme.objects.filter(user=user, scheme=self.scheme_ap).exists())

        # ── Step 10: Track Application ──
        resp_track = self.client.post(
            reverse('applications:add', kwargs={'scheme_slug': self.scheme_ap.slug}),
            follow=True
        )
        self.assertEqual(resp_track.status_code, 200)
        self.assertTrue(ApplicationTracker.objects.filter(user=user, scheme=self.scheme_ap).exists())

        # Update application status
        app_tracker = ApplicationTracker.objects.get(user=user, scheme=self.scheme_ap)
        resp_update_app = self.client.post(
            reverse('applications:update_status', kwargs={'pk': app_tracker.pk}),
            {'status': 'preparing_documents'},
            follow=True
        )
        self.assertEqual(resp_update_app.status_code, 200)
        app_tracker.refresh_from_db()
        self.assertEqual(app_tracker.status, 'preparing_documents')

        # ── Step 11: Document Checklist ──
        resp_docs = self.client.get(reverse('documents:overview'))
        self.assertEqual(resp_docs.status_code, 200)
        self.assertContains(resp_docs, 'పత్రాల జాబితా')

        # ── Step 12: Profile Page ──
        resp_prof = self.client.get(reverse('dashboard:profile'))
        self.assertEqual(resp_prof.status_code, 200)
        self.assertContains(resp_prof, 'K. Venkat Rao')
        self.assertContains(resp_prof, 'రైతు')

        # ── Step 13: Ask AI Assistant ──
        resp_ai = self.client.post(
            reverse('api_assistant:chat'),
            {'message': 'What documents do I need for Rythu Bharosa?', 'language': 'te'},
            content_type='application/json'
        )
        self.assertEqual(resp_ai.status_code, 200)
        data_ai = resp_ai.json()
        self.assertTrue(data_ai['success'])
        self.assertIn('response', data_ai)
