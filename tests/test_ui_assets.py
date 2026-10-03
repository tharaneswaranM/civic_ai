"""
Civic AI — Tests: UI Visual Asset Integration & Data-Driven Flow Verification
Validates that:
- Static image files exist on disk.
- State model dynamic property getters return correct paths for AP & TN.
- Landing page renders hero family and state choice cards.
- Transition page dynamically renders AP / TN visuals.
- Login page dynamically renders AP / TN login artwork and brand logo.
- Profile setup steps (1 to 5) render brand logo.
- Dashboard & Assistant render the Civic AI assistant mascot.
- Multilingual accessibility is preserved across English, Tamil, and Telugu.
"""
import os
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.utils import translation
from apps.states.models import State, District, Language
from apps.accounts.models import User
from apps.profiles.models import UserProfile


class UIAssetIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.en = Language.objects.create(code='en', name='English', native_name='English', display_order=1)
        cls.ta = Language.objects.create(code='ta', name='Tamil', native_name='தமிழ்', display_order=2)
        cls.te = Language.objects.create(code='te', name='Telugu', native_name='తెలుగు', display_order=3)

        cls.ap = State.objects.create(
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
        cls.ap.languages.set([cls.en, cls.te])
        cls.ap_dist = District.objects.create(state=cls.ap, name='Visakhapatnam', is_active=True)

        cls.tn = State.objects.create(
            code='TN',
            name='Tamil Nadu',
            native_name='தமிழ் நாடு',
            slug='tamil-nadu',
            transition_title='Welcome to Tamil Nadu',
            transition_subtitle='Personalized schemes for you.',
            transition_color_primary='#8B0000',
            transition_landmark='Meenakshi Amman Temple',
            display_order=2,
            is_active=True,
        )
        cls.tn.languages.set([cls.en, cls.ta])
        cls.tn_dist = District.objects.create(state=cls.tn, name='Chennai', is_active=True)

    def setUp(self):
        translation.activate('en')
        self.client = Client()

    def test_static_asset_files_exist(self):
        """Verify all 10 core generated UI assets exist in static/images/civic_ai/."""
        expected_assets = [
            'brand/logo.png',
            'brand/hero_family.png',
            'brand/mascot.png',
            'brand/cloud_bg.png',
            'states/ap_state.png',
            'states/ap_transition.png',
            'states/ap_login.png',
            'states/tn_state.png',
            'states/tn_transition.png',
            'states/tn_login.png',
        ]
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'civic_ai')
        for asset in expected_assets:
            file_path = os.path.join(static_dir, os.path.normpath(asset))
            self.assertTrue(os.path.exists(file_path), f"Asset missing on disk: {file_path}")
            self.assertGreater(os.path.getsize(file_path), 1000, f"Asset file is empty/too small: {file_path}")

    def test_state_model_image_properties(self):
        """Verify State model dynamic property getters return correct paths."""
        self.assertIn('ap_state.png', self.ap.card_image)
        self.assertIn('ap_transition.png', self.ap.transition_image)
        self.assertIn('ap_login.png', self.ap.login_image)

        self.assertIn('tn_state.png', self.tn.card_image)
        self.assertIn('tn_transition.png', self.tn.transition_image)
        self.assertIn('tn_login.png', self.tn.login_image)

    def test_landing_page_renders_hero_and_state_cards(self):
        """Landing page must render hero family image and both AP and TN cards."""
        resp = self.client.get(reverse('states:landing'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'images/civic_ai/brand/hero_family.png')
        self.assertContains(resp, 'images/civic_ai/brand/logo.png')
        self.assertContains(resp, 'images/civic_ai/brand/cloud_bg.png')
        self.assertContains(resp, 'images/civic_ai/states/ap_state.png')
        self.assertContains(resp, 'images/civic_ai/states/tn_state.png')

    def test_state_transition_page_ap_and_tn(self):
        """Transition page must dynamically render AP visual for AP, and TN visual for TN."""
        # AP transition
        resp_ap = self.client.get(reverse('states:state_transition', kwargs={'slug': 'andhra-pradesh'}))
        self.assertEqual(resp_ap.status_code, 200)
        self.assertContains(resp_ap, 'images/civic_ai/states/ap_transition.png')
        self.assertNotContains(resp_ap, 'images/civic_ai/states/tn_transition.png')

        # TN transition
        resp_tn = self.client.get(reverse('states:state_transition', kwargs={'slug': 'tamil-nadu'}))
        self.assertEqual(resp_tn.status_code, 200)
        self.assertContains(resp_tn, 'images/civic_ai/states/tn_transition.png')
        self.assertNotContains(resp_tn, 'images/civic_ai/states/ap_transition.png')

    def test_login_page_state_data_driven_images(self):
        """Login page must show AP login visual when AP is chosen, and TN when TN is chosen."""
        # 1. AP selected
        self.client.post(reverse('states:set_state'), {'state_slug': 'andhra-pradesh'})
        resp_ap = self.client.get(reverse('accounts:login'))
        self.assertEqual(resp_ap.status_code, 200)
        self.assertContains(resp_ap, 'images/civic_ai/states/ap_login.png')
        self.assertContains(resp_ap, 'images/civic_ai/brand/logo.png')
        self.assertContains(resp_ap, 'Andhra Pradesh')

        # 2. TN selected
        self.client.post(reverse('states:set_state'), {'state_slug': 'tamil-nadu'})
        resp_tn = self.client.get(reverse('accounts:login'))
        self.assertEqual(resp_tn.status_code, 200)
        self.assertContains(resp_tn, 'images/civic_ai/states/tn_login.png')
        self.assertContains(resp_tn, 'images/civic_ai/brand/logo.png')
        self.assertContains(resp_tn, 'Tamil Nadu')

    def test_profile_wizard_steps_render_logo(self):
        """Steps 1-5 in profile setup must include the brand logo."""
        # Create and log in a user with incomplete profile
        user = User.objects.create_user(mobile_number='+919876543210')
        self.client.force_login(user)

        for step in range(1, 6):
            url = reverse('dashboard:profile_setup_step', kwargs={'step': step})
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, f"Step {step} failed to render")
            self.assertContains(resp, 'images/civic_ai/brand/logo.png', msg_prefix=f"Step {step} missing logo")

    def test_dashboard_and_assistant_render_mascot(self):
        """Dashboard and Assistant must render the Civic AI assistant mascot."""
        user = User.objects.create_user(
            mobile_number='+919876543210',
            full_name='Test Citizen',
            preferred_language='en',
            is_profile_complete=True,
        )
        UserProfile.objects.create(
            user=user,
            state=self.ap,
            district=self.ap_dist,
            completion_percentage=100,
        )
        self.client.force_login(user)

        # Dashboard
        resp_dash = self.client.get(reverse('dashboard:home'))
        self.assertEqual(resp_dash.status_code, 200)
        self.assertContains(resp_dash, 'images/civic_ai/brand/mascot.png')

        # AI Assistant
        resp_asst = self.client.get(reverse('assistant:chat'))
        self.assertEqual(resp_asst.status_code, 200)
        self.assertContains(resp_asst, 'images/civic_ai/brand/mascot.png')

    def test_multilingual_flow_renders_properly(self):
        """Verify English, Tamil, and Telugu views render with the visual assets."""
        for path in ['/', '/ta/', '/te/']:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200, f"Landing failed at {path}")
            self.assertContains(resp, 'images/civic_ai/brand/hero_family.png')
            self.assertContains(resp, 'images/civic_ai/brand/logo.png')
