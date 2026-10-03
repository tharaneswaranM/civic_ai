"""
Civic AI — Tests: Eligibility Engine (Deterministic Rules)
"""
from django.test import TestCase
from apps.accounts.models import User
from apps.states.models import State, Language
from apps.profiles.models import UserProfile
from apps.schemes.models import Scheme, SchemeVersion, EligibilityRule, UserSchemeMatch
from apps.eligibility.engine import EligibilityEngine, run_eligibility_for_user


class EligibilityEngineTests(TestCase):
    def setUp(self):
        self.engine = EligibilityEngine()

        # Languages & States
        self.en = Language.objects.create(code='en', name='English', native_name='English')
        self.te = Language.objects.create(code='te', name='Telugu', native_name='తెలుగు')

        self.ap = State.objects.create(code='AP', name='Andhra Pradesh', native_name='ఆంధ్ర ప్రదేశ్', slug='andhra-pradesh')
        self.tn = State.objects.create(code='TN', name='Tamil Nadu', native_name='தமிழ் நாடு', slug='tamil-nadu')

        # User & Profile
        self.user = User.objects.create(mobile_number='+919876543210', full_name='Satya Rao')
        self.profile = UserProfile.objects.create(
            user=self.user,
            state=self.ap,
            age=28,
            gender='male',
            education_level='graduate',
            employment_status='farmer',
            individual_income_range='1l_2_5l',
            family_income_range='2_5l_5l',
            is_farmer=True,
            is_student=False,
            category='obc',
        )

        # Create Scheme with Version
        self.scheme = Scheme.objects.create(
            name='AP Farmer Welfare Scheme',
            slug='ap-farmer-welfare',
            level='state',
            state=self.ap,
            status=Scheme.STATUS_ACTIVE,
        )
        self.version = SchemeVersion.objects.create(
            scheme=self.scheme,
            version_number=1,
            description='Support for AP farmers under 40 years old.',
            benefit_summary='Rs 10,000 per season.',
            review_status='approved',
        )
        self.scheme.current_version = self.version
        self.scheme.save()

    def test_eligible_when_all_rules_pass(self):
        # Rules: state=AP, is_farmer=True, max_age=40, max_individual_income=500000
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_STATE,
            value='AP',
            is_mandatory=True,
        )
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_IS_FARMER,
            value='true',
            is_mandatory=True,
        )
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_MAX_AGE,
            value='40',
            is_mandatory=True,
        )
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_MAX_INDIVIDUAL_INCOME,
            value='500000',
            is_mandatory=True,
        )

        result = self.engine.evaluate(self.profile, self.scheme)
        self.assertEqual(result.result, UserSchemeMatch.RESULT_ELIGIBLE)
        self.assertTrue(result.is_eligible)
        self.assertEqual(len(result.missing_info), 0)

    def test_not_eligible_when_state_mismatches(self):
        # Rule requires Tamil Nadu
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_STATE,
            value='TN',
            is_mandatory=True,
            display_label='Tamil Nadu Resident',
        )
        result = self.engine.evaluate(self.profile, self.scheme)
        self.assertEqual(result.result, UserSchemeMatch.RESULT_NOT_ELIGIBLE)
        self.assertFalse(result.is_eligible)

    def test_not_eligible_when_age_exceeds_max(self):
        # Rule: max age 25 (user is 28)
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_MAX_AGE,
            value='25',
            is_mandatory=True,
        )
        result = self.engine.evaluate(self.profile, self.scheme)
        self.assertEqual(result.result, UserSchemeMatch.RESULT_NOT_ELIGIBLE)

    def test_incomplete_when_profile_field_missing(self):
        # Create user with blank profile
        new_user = User.objects.create(mobile_number='+919000000000')
        empty_profile = UserProfile.objects.create(user=new_user)

        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_MIN_AGE,
            value='18',
            is_mandatory=True,
        )
        result = self.engine.evaluate(empty_profile, self.scheme)
        self.assertEqual(result.result, UserSchemeMatch.RESULT_INCOMPLETE)
        self.assertIn('min_age', result.missing_info)

    def test_education_order_comparison(self):
        # User is 'graduate' (rank 6)
        # Rule: minimum education 'higher_secondary' (rank 4) -> should pass
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_EDUCATION_MIN,
            value='higher_secondary',
            is_mandatory=True,
        )
        result = self.engine.evaluate(self.profile, self.scheme)
        self.assertEqual(result.result, UserSchemeMatch.RESULT_ELIGIBLE)

        # Rule: minimum education 'doctorate' (rank 8) -> should fail
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_EDUCATION_MIN,
            value='doctorate',
            is_mandatory=True,
        )
        result2 = self.engine.evaluate(self.profile, self.scheme)
        self.assertEqual(result2.result, UserSchemeMatch.RESULT_NOT_ELIGIBLE)

    def test_batch_re_evaluation(self):
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_STATE,
            value='AP',
            is_mandatory=True,
        )
        run_eligibility_for_user(self.user)
        match = UserSchemeMatch.objects.filter(user=self.user, scheme=self.scheme).first()
        self.assertIsNotNone(match)
        self.assertEqual(match.result, UserSchemeMatch.RESULT_ELIGIBLE)

    def test_age_calculated_from_dob_fallback(self):
        """When profile.age is None, engine computes age from date_of_birth."""
        from datetime import date
        dob_user = User.objects.create(mobile_number='+919111111111')
        dob_profile = UserProfile.objects.create(
            user=dob_user,
            state=self.ap,
            date_of_birth=date(1995, 5, 10),
            age=None,
        )
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_MIN_AGE,
            value='18',
            is_mandatory=True,
        )
        result = self.engine.evaluate(dob_profile, self.scheme)
        self.assertEqual(result.result, UserSchemeMatch.RESULT_ELIGIBLE)
        self.assertEqual(len(result.missing_info), 0)

    def test_mandatory_fail_takes_precedence_over_missing_info(self):
        """If a mandatory rule fails, overall result must be NOT_ELIGIBLE even if optional fields are missing."""
        # Rule 1: state=TN (User is AP -> FAILS)
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_STATE,
            value='TN',
            is_mandatory=True,
        )
        # Rule 2: has_disability (User has_disability=None -> missing info)
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_HAS_DISABILITY,
            value='true',
            is_mandatory=True,
        )
        result = self.engine.evaluate(self.profile, self.scheme)
        self.assertEqual(result.result, UserSchemeMatch.RESULT_NOT_ELIGIBLE)

    def test_optional_rule_missing_info_does_not_block_eligibility(self):
        """Non-mandatory rule missing info does not make scheme evaluation incomplete if mandatory pass."""
        # Mandatory rule: state=AP (Passes)
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_STATE,
            value='AP',
            is_mandatory=True,
        )
        # Optional rule: is_shg_member (None in profile, is_mandatory=False)
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_IS_SHG_MEMBER,
            value='true',
            is_mandatory=False,
        )
        result = self.engine.evaluate(self.profile, self.scheme)
        self.assertEqual(result.result, UserSchemeMatch.RESULT_ELIGIBLE)
        self.assertEqual(len(result.missing_info), 0)

    def test_unknown_mandatory_rule_fails_closed(self):
        rule = EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type='unsupported_rule',
            value='anything',
            is_mandatory=True,
        )

        result = self.engine.evaluate(self.profile, self.scheme)

        self.assertEqual(result.result, UserSchemeMatch.RESULT_NOT_ELIGIBLE)
        self.assertEqual(result.configuration_errors, ['unsupported_rule'])
        failed = next(item for item in result.rule_results if item.rule_type == rule.rule_type)
        self.assertFalse(failed.passed)
        self.assertEqual(failed.reason, 'configuration_error')

        saved = self.engine.evaluate_and_save(self.user, self.profile, self.scheme)
        self.assertEqual(saved.result, UserSchemeMatch.RESULT_NOT_ELIGIBLE)
        unsupported_result = next(
            item for item in saved.matched_rules
            if item['rule_type'] == 'unsupported_rule'
        )
        self.assertEqual(unsupported_result['reason'], 'configuration_error')

    def test_malformed_mandatory_threshold_fails_closed(self):
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_MAX_AGE,
            value='not-a-number',
            is_mandatory=True,
        )

        result = self.engine.evaluate(self.profile, self.scheme)

        self.assertEqual(result.result, UserSchemeMatch.RESULT_NOT_ELIGIBLE)
        self.assertEqual(result.configuration_errors, [EligibilityRule.RULE_MAX_AGE])

    def test_invalid_boolean_rule_fails_closed(self):
        EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_IS_FARMER,
            value='perhaps',
            is_mandatory=True,
        )

        result = self.engine.evaluate(self.profile, self.scheme)

        self.assertEqual(result.result, UserSchemeMatch.RESULT_NOT_ELIGIBLE)
        self.assertEqual(result.configuration_errors, [EligibilityRule.RULE_IS_FARMER])

    def test_minimum_and_maximum_age_boundaries(self):
        EligibilityRule.objects.create(
            scheme_version=self.version, rule_type=EligibilityRule.RULE_MIN_AGE,
            value='28', is_mandatory=True,
        )
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_ELIGIBLE)
        self.profile.age = 27
        self.profile.save(update_fields=['age'])
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_NOT_ELIGIBLE)

        EligibilityRule.objects.all().delete()
        self.profile.age = 28
        self.profile.save(update_fields=['age'])
        EligibilityRule.objects.create(
            scheme_version=self.version, rule_type=EligibilityRule.RULE_MAX_AGE,
            value='28', is_mandatory=True,
        )
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_ELIGIBLE)
        self.profile.age = 29
        self.profile.save(update_fields=['age'])
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_NOT_ELIGIBLE)

    def test_income_threshold_includes_exact_limit_and_rejects_one_unit_above(self):
        self.profile.individual_income_range = UserProfile.INCOME_BELOW_1L
        self.profile.save(update_fields=['individual_income_range'])
        rule = EligibilityRule.objects.create(
            scheme_version=self.version,
            rule_type=EligibilityRule.RULE_MAX_INDIVIDUAL_INCOME,
            value='100000', is_mandatory=True,
        )
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_ELIGIBLE)
        rule.value = '99999'
        rule.save(update_fields=['value'])
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_NOT_ELIGIBLE)

    def test_education_min_and_max_equality_boundaries(self):
        minimum = EligibilityRule.objects.create(
            scheme_version=self.version, rule_type=EligibilityRule.RULE_EDUCATION_MIN,
            value=UserProfile.EDUCATION_GRADUATE, is_mandatory=True,
        )
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_ELIGIBLE)
        self.profile.education_level = UserProfile.EDUCATION_HIGHER_SECONDARY
        self.profile.save(update_fields=['education_level'])
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_NOT_ELIGIBLE)
        minimum.delete()

        self.profile.education_level = UserProfile.EDUCATION_GRADUATE
        self.profile.save(update_fields=['education_level'])
        EligibilityRule.objects.create(
            scheme_version=self.version, rule_type=EligibilityRule.RULE_EDUCATION_MAX,
            value=UserProfile.EDUCATION_GRADUATE, is_mandatory=True,
        )
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_ELIGIBLE)
        self.profile.education_level = UserProfile.EDUCATION_POSTGRADUATE
        self.profile.save(update_fields=['education_level'])
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_NOT_ELIGIBLE)

    def test_central_scheme_is_not_limited_by_profile_state(self):
        central = Scheme.objects.create(
            name='Central Test Scheme', slug='central-test-scheme',
            level=Scheme.LEVEL_CENTRAL, status=Scheme.STATUS_ACTIVE,
        )
        version = SchemeVersion.objects.create(
            scheme=central, version_number=1, description='Central scheme',
            review_status='approved',
        )
        central.current_version = version
        central.save(update_fields=['current_version'])
        for state in (self.ap, self.tn):
            with self.subTest(state=state.code):
                self.profile.state = state
                self.profile.save(update_fields=['state'])
                self.assertEqual(self.engine.evaluate(self.profile, central).result,
                                 UserSchemeMatch.RESULT_ELIGIBLE)

    def test_state_scheme_rejects_a_profile_from_another_state(self):
        self.scheme.state = self.tn
        self.scheme.save(update_fields=['state'])
        self.profile.state = self.ap
        self.profile.save(update_fields=['state'])
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_NOT_ELIGIBLE)
        self.profile.state = self.tn
        self.profile.save(update_fields=['state'])
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_ELIGIBLE)

    def test_district_rule_matches_configured_district_and_rejects_another(self):
        from apps.states.models import District
        chennai = District.objects.create(state=self.tn, name='Chennai', code='TN-CHN')
        coimbatore = District.objects.create(state=self.tn, name='Coimbatore', code='TN-CBE')
        self.scheme.state = self.tn
        self.scheme.level = Scheme.LEVEL_DISTRICT
        self.scheme.save(update_fields=['state', 'level'])
        self.profile.state = self.tn
        self.profile.district = chennai
        self.profile.save(update_fields=['state', 'district'])
        EligibilityRule.objects.create(
            scheme_version=self.version, rule_type='district',
            value='TN-CHN', is_mandatory=True,
        )
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_ELIGIBLE)
        self.profile.district = coimbatore
        self.profile.save(update_fields=['district'])
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_NOT_ELIGIBLE)

    def test_district_level_scheme_without_mandatory_district_rule_fails_closed(self):
        self.scheme.level = Scheme.LEVEL_DISTRICT
        self.scheme.save(update_fields=['level'])
        result = self.engine.evaluate(self.profile, self.scheme)
        self.assertEqual(result.result, UserSchemeMatch.RESULT_NOT_ELIGIBLE)
        self.assertIn('district_scope', result.configuration_errors)

    def test_unknown_district_configuration_fails_closed(self):
        self.scheme.level = Scheme.LEVEL_DISTRICT
        self.scheme.save(update_fields=['level'])
        EligibilityRule.objects.create(
            scheme_version=self.version, rule_type=EligibilityRule.RULE_DISTRICT,
            value='UNKNOWN-DISTRICT', is_mandatory=True,
        )
        result = self.engine.evaluate(self.profile, self.scheme)
        self.assertEqual(result.result, UserSchemeMatch.RESULT_NOT_ELIGIBLE)
        self.assertIn(EligibilityRule.RULE_DISTRICT, result.configuration_errors)

    def test_missing_mandatory_citizen_field_is_incomplete(self):
        self.profile.gender = ''
        self.profile.save(update_fields=['gender'])
        EligibilityRule.objects.create(
            scheme_version=self.version, rule_type=EligibilityRule.RULE_GENDER,
            value='female', is_mandatory=True,
        )
        self.assertEqual(self.engine.evaluate(self.profile, self.scheme).result,
                         UserSchemeMatch.RESULT_INCOMPLETE)
