"""
Civic AI — Tests: States, Language Switching, and Onboarding Flow
"""
from django.test import TestCase, Client
from django.utils import translation
from django.core.cache import cache
from django.urls import reverse
from apps.states.models import State, Language
from apps.accounts.models import User
from apps.accounts.otp.service import OTPService


class StatesAndOnboardingTests(TestCase):
    def setUp(self):
        # Requests activate their selected language; reset the thread-local
        # translation before building URLs so test order cannot leak locales.
        translation.activate('en')
        cache.clear()
        self.client = Client()
        self.en = Language.objects.create(code='en', name='English', native_name='English', display_order=1)
        self.ta = Language.objects.create(code='ta', name='Tamil', native_name='தமிழ்', display_order=2)
        self.te = Language.objects.create(code='te', name='Telugu', native_name='తెలుగు', display_order=3)

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

        self.tn = State.objects.create(
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
        self.tn.languages.set([self.en, self.ta])

    def test_landing_page_renders_active_states(self):
        resp = self.client.get(reverse('states:landing'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Andhra Pradesh')
        self.assertContains(resp, 'Tamil Nadu')

    def test_state_selection_and_transition(self):
        # This test checks the English transition copy despite AP's Telugu
        # suggestion, so establish an explicit language choice first.
        self.client.post(reverse('states:set_language'), {'language_code': 'en'})
        # User selects Andhra Pradesh
        resp = self.client.post(reverse('states:set_state'), {'state_slug': 'andhra-pradesh'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        # Should show transition page
        self.assertContains(resp, 'Welcome to Andhra Pradesh')
        self.assertContains(resp, 'Tirumala Venkateswara Temple')
        # Session should remember selected state
        self.assertEqual(self.client.session.get('selected_state'), 'andhra-pradesh')

    def test_language_selection(self):
        resp = self.client.post(reverse('states:set_language'), {'language_code': 'te'}, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.client.session.get('selected_language'), 'te')
        self.assertEqual(resp.cookies['django_language'].value, 'te')
        self.assertIn('/te/auth/login/', resp.url)

    def test_state_suggests_language_but_offers_every_supported_language(self):
        self.client.post(reverse('states:set_state'), {'state_slug': 'andhra-pradesh'})
        resp = self.client.get(reverse('states:state_transition', args=['andhra-pradesh']))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.wsgi_request.LANGUAGE_CODE, 'te')
        offered_codes = {language.code for language in resp.context['languages']}
        self.assertEqual(offered_codes, {'en', 'ta', 'te'})
        self.assertEqual(resp.context['suggested_language'], 'te')

    def test_selected_language_survives_followup_requests(self):
        self.client.post(reverse('states:set_language'), {'language_code': 'ta'})

        resp = self.client.get(reverse('accounts:login'))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.wsgi_request.LANGUAGE_CODE, 'ta')
        self.assertEqual(resp.context['selected_language'], 'ta')

    def test_explicit_language_choice_overrides_each_state_suggestion(self):
        for state_slug, language in (
            ('andhra-pradesh', 'en'),
            ('andhra-pradesh', 'ta'),
            ('andhra-pradesh', 'te'),
            ('tamil-nadu', 'en'),
            ('tamil-nadu', 'ta'),
            ('tamil-nadu', 'te'),
        ):
            with self.subTest(state=state_slug, language=language):
                self.client.post(reverse('states:set_state'), {'state_slug': state_slug})
                self.client.post(reverse('states:set_language'), {'language_code': language})
                response = self.client.get(reverse('accounts:login'))
                self.assertEqual(response.wsgi_request.LANGUAGE_CODE, language)

    def test_login_keeps_existing_account_language_preference(self):
        user = User.objects.create(
            mobile_number='+919876543210',
            preferred_language='ta',
            is_profile_complete=True,
        )
        session = self.client.session
        session['pending_mobile'] = user.mobile_number
        session['selected_language'] = 'en'
        session.save()
        OTPService().send_otp(user.mobile_number, purpose='login')

        response = self.client.post(reverse('accounts:verify_otp_submit'), {
            'otp_1': '1', 'otp_2': '2', 'otp_3': '3',
            'otp_4': '4', 'otp_5': '5', 'otp_6': '6',
        })

        user.refresh_from_db()
        self.assertEqual(user.preferred_language, 'ta')
        self.assertEqual(response.cookies['django_language'].value, 'ta')
        self.assertIn('/ta/', response.url)

        self.client.post(reverse('accounts:logout'))
        login_page = self.client.get(reverse('accounts:login'))
        self.assertEqual(login_page.wsgi_request.LANGUAGE_CODE, 'ta')
        cache.clear()  # Isolate the second login from the first send's cooldown.
        self.client.post(reverse('accounts:send_otp'), {'mobile_number': '9876543210'})
        relogin = self.client.post(reverse('accounts:verify_otp_submit'), {
            'otp_1': '1', 'otp_2': '2', 'otp_3': '3',
            'otp_4': '4', 'otp_5': '5', 'otp_6': '6',
        })
        self.assertEqual(relogin.cookies['django_language'].value, 'ta')
        user.refresh_from_db()
        self.assertEqual(user.preferred_language, 'ta')

    def _assert_new_user_onboarding_language(self, state_slug, language, mobile, localized_text):
        self.client.post(reverse('states:set_state'), {'state_slug': state_slug})
        self.client.post(reverse('states:set_language'), {'language_code': language})
        self.client.post(reverse('accounts:send_otp'), {'mobile_number': mobile})
        response = self.client.post(reverse('accounts:verify_otp_submit'), {
            'otp_1': '1', 'otp_2': '2', 'otp_3': '3',
            'otp_4': '4', 'otp_5': '5', 'otp_6': '6',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, language)
        self.assertEqual(response.wsgi_request.session['selected_language'], language)
        self.assertContains(response, localized_text)
        user = User.objects.get(mobile_number=f'+91{mobile}')
        self.assertEqual(user.preferred_language, language)

        user.is_profile_complete = True
        user.save(update_fields=['is_profile_complete'])
        dashboard = self.client.get(reverse('dashboard:home'))
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.wsgi_request.LANGUAGE_CODE, language)

    def test_ap_telugu_language_is_kept_through_otp_profile_and_dashboard(self):
        self._assert_new_user_onboarding_language(
            'andhra-pradesh', 'te', '9876543210', 'వ్యక్తిగత సమాచారం'
        )

    def test_tn_tamil_language_is_kept_through_otp_profile_and_dashboard(self):
        self._assert_new_user_onboarding_language(
            'tamil-nadu', 'ta', '9876543211', 'தனிப்பட்ட தகவல்கள்'
        )

    def test_states_api(self):
        resp = self.client.get(reverse('api_states:list'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('states', data)
        self.assertEqual(len(data['states']), 2)
        codes = [s['code'] for s in data['states']]
        self.assertIn('AP', codes)
        self.assertIn('TN', codes)

    def test_recent_priority_catalog_messages_are_compiled(self):
        with translation.override('ta'):
            self.assertEqual(
                translation.gettext('Date of birth cannot be in the future.'),
                'பிறந்த தேதி எதிர்காலத்தில் இருக்க முடியாது.',
            )
            self.assertEqual(translation.gettext('Scheme saved!'), 'திட்டம் சேமிக்கப்பட்டது!')
        with translation.override('te'):
            self.assertEqual(
                translation.gettext('Date of birth cannot be in the future.'),
                'పుట్టిన తేదీ భవిష్యత్తులో ఉండకూడదు.',
            )
            self.assertEqual(translation.gettext('Scheme saved!'), 'పథకం సేవ్ చేయబడింది!')

    def test_default_tamil_and_telugu_routes_and_login_routes(self):
        for path in ('/', '/ta/', '/te/', '/auth/login/', '/ta/auth/login/', '/te/auth/login/'):
            with self.subTest(path=path):
                response = Client().get(path)
                self.assertEqual(response.status_code, 200)

    def test_added_priority_ui_catalogs_render_in_tamil_and_telugu(self):
        tamil_landing = self.client.get('/ta/')
        self.assertEqual(tamil_landing.status_code, 200)
        self.assertContains(tamil_landing, 'திட்டங்களைக் கண்டறியவும்')

        telugu_landing = self.client.get('/te/')
        self.assertEqual(telugu_landing.status_code, 200)
        self.assertContains(telugu_landing, 'పథకాలను కనుగొనండి')

        tamil_user = User.objects.create_user(
            mobile_number='+919876543299', preferred_language='ta'
        )
        tamil_client = Client()
        tamil_client.force_login(tamil_user)
        tamil_profile = tamil_client.get('/ta/dashboard/setup/1/')
        self.assertEqual(tamil_profile.status_code, 200)
        self.assertContains(tamil_profile, 'முழுப் பெயர்')

        telugu_user = User.objects.create_user(
            mobile_number='+919876543298', preferred_language='te'
        )
        telugu_client = Client()
        telugu_client.force_login(telugu_user)
        telugu_profile = telugu_client.get('/te/dashboard/setup/1/')
        self.assertEqual(telugu_profile.status_code, 200)
        self.assertContains(telugu_profile, 'పూర్తి పేరు')


class AssistantAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(mobile_number='+919876543210', full_name='Test User')
        self.client.force_login(self.user)

    def test_assistant_chat_api(self):
        resp = self.client.post(
            reverse('api_assistant:chat'),
            {'message': 'Which schemes am I eligible for?', 'language': 'en'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertIn('response', data)
        self.assertIn('conversation_id', data)

    def test_assistant_replies_in_requested_supported_language(self):
        samples = {
            'en': 'Based on your profile, I can see potential matches for government schemes.',
            'ta': 'உங்கள் சுயவிவரத்தின் அடிப்படையில், உங்களுக்குப் பொருந்தக்கூடிய அரசுத் திட்டங்கள் இருக்கலாம்.',
            'te': 'మీ ప్రొఫైల్ ఆధారంగా మీకు సరిపడే ప్రభుత్వ పథకాలు ఉండవచ్చు.',
        }
        for language, expected in samples.items():
            with self.subTest(language=language):
                response = self.client.post(
                    reverse('api_assistant:chat'),
                    {'message': 'eligible', 'language': language},
                    content_type='application/json',
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(expected, response.json()['response'])
