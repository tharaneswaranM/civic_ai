"""
Civic AI — Eligibility Engine
Deterministic, testable eligibility matching engine.

IMPORTANT: The LLM does NOT decide eligibility.
The engine evaluates structured rules against the user profile.
The LLM is only used to EXPLAIN the result afterwards.
"""
import logging
from dataclasses import dataclass, field
from apps.profiles.models import UserProfile
from apps.schemes.models import Scheme, SchemeVersion, EligibilityRule, UserSchemeMatch
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


# ─── Result Types ─────────────────────────────────────────────────────────────

@dataclass
class RuleResult:
    """Result of evaluating a single eligibility rule."""
    rule_type: str
    passed: bool
    is_mandatory: bool
    display_label: str
    user_value: str = ''
    required_value: str = ''
    reason: str = ''


@dataclass
class EligibilityResult:
    """Overall result of evaluating all rules for one scheme."""
    scheme_id: str
    scheme_name: str
    result: str  # 'eligible' | 'incomplete' | 'not_eligible'
    rule_results: list = field(default_factory=list)
    missing_info: list = field(default_factory=list)
    configuration_errors: list = field(default_factory=list)
    summary: str = ''

    @property
    def is_eligible(self):
        return self.result == UserSchemeMatch.RESULT_ELIGIBLE

    @property
    def is_incomplete(self):
        return self.result == UserSchemeMatch.RESULT_INCOMPLETE

    def passed_rules(self):
        return [r for r in self.rule_results if r.passed]

    def failed_rules(self):
        return [r for r in self.rule_results if not r.passed and r.is_mandatory]


# ─── Education Level Ordering ─────────────────────────────────────────────────

EDUCATION_ORDER = {
    UserProfile.EDUCATION_NO_FORMAL: 0,
    UserProfile.EDUCATION_PRIMARY: 1,
    UserProfile.EDUCATION_MIDDLE: 2,
    UserProfile.EDUCATION_SECONDARY: 3,
    UserProfile.EDUCATION_HIGHER_SECONDARY: 4,
    UserProfile.EDUCATION_DIPLOMA: 5,
    UserProfile.EDUCATION_GRADUATE: 6,
    UserProfile.EDUCATION_POSTGRADUATE: 7,
    UserProfile.EDUCATION_DOCTORATE: 8,
}


# ─── Engine ───────────────────────────────────────────────────────────────────

class EligibilityEngine:
    """
    Evaluates eligibility rules for a user profile against scheme versions.
    
    Usage:
        engine = EligibilityEngine()
        result = engine.evaluate(profile, scheme)
        # result.result in ['eligible', 'incomplete', 'not_eligible']
    """

    def evaluate(self, profile: UserProfile, scheme: Scheme) -> EligibilityResult:
        """
        Evaluate a user profile against a scheme's eligibility rules.
        Returns an EligibilityResult.
        """
        version = scheme.current_version
        if not version:
            return EligibilityResult(
                scheme_id=str(scheme.id),
                scheme_name=scheme.name,
                result=UserSchemeMatch.RESULT_INCOMPLETE,
                summary='Eligibility rules not yet configured for this scheme.',
            )

        rules = list(version.eligibility_rules.all())
        rule_results = self._evaluate_scheme_scope(profile, scheme, rules)
        rule_results.extend(self._evaluate_rule(rule, profile) for rule in rules)
        missing_info = []
        configuration_errors = []
        all_mandatory_passed = True

        for result in rule_results:
            if result.reason == 'configuration_error':
                configuration_errors.append(result.rule_type)

            if not result.passed:
                if result.reason == 'missing_info':
                    if result.is_mandatory:
                        missing_info.append(result.rule_type)
                elif result.is_mandatory:
                    all_mandatory_passed = False

        # Determine overall result:
        # 1. A failed mandatory rule definitively renders user not eligible
        # 2. Missing mandatory profile fields mark evaluation as incomplete
        # 3. Otherwise all mandatory conditions passed
        if not all_mandatory_passed:
            overall = UserSchemeMatch.RESULT_NOT_ELIGIBLE
        elif missing_info:
            overall = UserSchemeMatch.RESULT_INCOMPLETE
        else:
            overall = UserSchemeMatch.RESULT_ELIGIBLE

        return EligibilityResult(
            scheme_id=str(scheme.id),
            scheme_name=scheme.name,
            result=overall,
            rule_results=rule_results,
            missing_info=missing_info,
            configuration_errors=configuration_errors,
            summary=self._generate_summary(overall, rule_results, missing_info)
            + (' Scheme rules require administrative review.' if configuration_errors else ''),
        )

    def _evaluate_scheme_scope(self, profile, scheme, rules):
        """Apply geographic scope independently of optional scheme rules."""
        results = []
        if scheme.level in (Scheme.LEVEL_STATE, Scheme.LEVEL_DISTRICT):
            if not scheme.state_id:
                results.append(RuleResult(
                    rule_type='scheme_state', passed=False, is_mandatory=True,
                    display_label=_('Scheme state'), reason='configuration_error',
                ))
            elif not profile.state_id:
                results.append(RuleResult(
                    rule_type='state', passed=False, is_mandatory=True,
                    display_label=_('State'), reason='missing_info',
                ))
            else:
                results.append(RuleResult(
                    rule_type='scheme_state',
                    passed=(profile.state_id == scheme.state_id),
                    is_mandatory=True,
                    display_label=_('State'),
                    user_value=profile.state.code,
                    required_value=scheme.state.code,
                ))

        if scheme.level == Scheme.LEVEL_DISTRICT and not any(
            rule.rule_type == EligibilityRule.RULE_DISTRICT and rule.is_mandatory
            for rule in rules
        ):
            results.append(RuleResult(
                rule_type='district_scope', passed=False, is_mandatory=True,
                display_label=_('Scheme district'), reason='configuration_error',
            ))

        return results

    def evaluate_and_save(self, user, profile: UserProfile, scheme: Scheme) -> UserSchemeMatch:
        """Evaluate and persist the result to the database."""
        result = self.evaluate(profile, scheme)

        match, _ = UserSchemeMatch.objects.update_or_create(
            user=user,
            scheme=scheme,
            defaults={
                'scheme_version': scheme.current_version,
                'result': result.result,
                'matched_rules': [
                    {
                        'rule_type': r.rule_type,
                        'passed': r.passed,
                        'label': r.display_label,
                        'reason': r.reason,
                    }
                    for r in result.rule_results
                ],
                'missing_info': result.missing_info,
            }
        )
        return match

    def _evaluate_rule(self, rule: EligibilityRule, profile: UserProfile) -> RuleResult:
        """Dispatch to the appropriate rule evaluator."""
        handlers = {
            EligibilityRule.RULE_MIN_AGE: self._check_min_age,
            EligibilityRule.RULE_MAX_AGE: self._check_max_age,
            EligibilityRule.RULE_GENDER: self._check_gender,
            EligibilityRule.RULE_STATE: self._check_state,
            EligibilityRule.RULE_DISTRICT: self._check_district,
            EligibilityRule.RULE_MAX_INDIVIDUAL_INCOME: self._check_max_individual_income,
            EligibilityRule.RULE_MAX_FAMILY_INCOME: self._check_max_family_income,
            EligibilityRule.RULE_EDUCATION_MIN: self._check_education_min,
            EligibilityRule.RULE_EDUCATION_MAX: self._check_education_max,
            EligibilityRule.RULE_EMPLOYMENT_STATUS: self._check_employment_status,
            EligibilityRule.RULE_IS_FARMER: self._check_is_farmer,
            EligibilityRule.RULE_IS_STUDENT: self._check_is_student,
            EligibilityRule.RULE_HAS_DISABILITY: self._check_has_disability,
            EligibilityRule.RULE_IS_SENIOR: self._check_is_senior,
            EligibilityRule.RULE_IS_WIDOW: self._check_is_widow,
            EligibilityRule.RULE_CATEGORY: self._check_category,
            EligibilityRule.RULE_LAND_HOLDING: self._check_land_holding,
            EligibilityRule.RULE_MARITAL_STATUS: self._check_marital_status,
            EligibilityRule.RULE_IS_RURAL: self._check_is_rural,
            EligibilityRule.RULE_IS_JOB_SEEKER: self._check_is_job_seeker,
            EligibilityRule.RULE_IS_ENTREPRENEUR: self._check_is_entrepreneur,
            EligibilityRule.RULE_IS_SHG_MEMBER: self._check_is_shg_member,
        }

        handler = handlers.get(rule.rule_type)
        if handler:
            return handler(rule, profile)

        return self._configuration_error(rule, 'unsupported_rule_type')

    def _configuration_error(self, rule, code):
        logger.error(
            'Eligibility configuration error: rule_id=%s type=%s code=%s',
            rule.pk,
            rule.rule_type,
            code,
        )
        return RuleResult(
            rule_type=rule.rule_type,
            passed=False,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or rule.rule_type,
            reason='configuration_error',
        )

    def _nonnegative_integer_value(self, rule):
        try:
            value = int(rule.value)
        except (ValueError, TypeError, OverflowError):
            return None
        if value < 0:
            return None
        return value

    # ─── Individual Rule Checkers ─────────────────────────────────────────────

    def _get_user_age(self, profile):
        if profile.age is not None:
            return profile.age
        if getattr(profile, 'date_of_birth', None):
            from django.utils import timezone
            today = timezone.now().date()
            dob = profile.date_of_birth
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return None

    def _check_min_age(self, rule, profile):
        age = self._get_user_age(profile)
        if age is None:
            return self._missing('min_age', rule, 'Age not provided')
        required = self._nonnegative_integer_value(rule)
        if required is None:
            return self._configuration_error(rule, 'invalid_min_age')
        passed = age >= required
        return RuleResult(
            rule_type='min_age', passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or f'Age {required}+',
            user_value=str(age),
            required_value=f'>= {required}',
        )

    def _check_max_age(self, rule, profile):
        age = self._get_user_age(profile)
        if age is None:
            return self._missing('max_age', rule, 'Age not provided')
        required = self._nonnegative_integer_value(rule)
        if required is None:
            return self._configuration_error(rule, 'invalid_max_age')
        passed = age <= required
        return RuleResult(
            rule_type='max_age', passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or f'Age up to {required}',
            user_value=str(age),
            required_value=f'<= {required}',
        )

    def _check_gender(self, rule, profile):
        allowed_values = {value for value, _label in UserProfile.GENDER_CHOICES}
        allowed = [value.strip() for value in rule.value.split(',') if value.strip()]
        if not allowed or not set(allowed).issubset(allowed_values):
            return self._configuration_error(rule, 'invalid_gender_value')
        if not profile.gender:
            return self._missing('gender', rule, 'Gender not specified')
        # Allow comma-separated: "female,other"
        passed = profile.gender in allowed
        return RuleResult(
            rule_type='gender', passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or 'Gender',
            user_value=profile.gender,
            required_value=', '.join(allowed),
        )

    def _check_state(self, rule, profile):
        if not profile.state:
            return self._missing('state', rule, 'State not set')
        allowed = [v.strip() for v in rule.value.split(',')]
        passed = profile.state.code in allowed
        return RuleResult(
            rule_type='state', passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or 'State',
            user_value=profile.state.code,
            required_value=', '.join(allowed),
        )

    def _check_district(self, rule, profile):
        from apps.states.models import District

        allowed = [value.strip() for value in rule.value.split(',') if value.strip()]
        if not allowed:
            return self._configuration_error(rule, 'invalid_district_value')

        valid_values = set()
        for district in District.objects.filter(is_active=True).only('id', 'code', 'name'):
            valid_values.add(str(district.pk).casefold())
            valid_values.add(district.name.strip().casefold())
            if district.code:
                valid_values.add(district.code.strip().casefold())
        normalized_allowed = {value.casefold() for value in allowed}
        if not normalized_allowed.issubset(valid_values):
            return self._configuration_error(rule, 'unknown_district_value')

        district = getattr(profile, 'district', None)
        if not district or not profile.state_id:
            return self._missing('district', rule, 'District not set')
        if district.state_id != profile.state_id:
            return self._missing('district', rule, 'District does not match the selected state')

        identifiers = {str(district.pk).casefold(), district.name.strip().casefold()}
        if district.code:
            identifiers.add(district.code.strip().casefold())
        return RuleResult(
            rule_type=EligibilityRule.RULE_DISTRICT,
            passed=bool(identifiers & normalized_allowed),
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or _('District'),
            user_value=district.code or district.name,
            required_value=', '.join(allowed),
        )

    def _check_max_individual_income(self, rule, profile):
        if not profile.individual_income_range:
            return self._missing('individual_income_range', rule, 'Income range not provided')
        if profile.individual_income_range not in UserProfile.INCOME_VALUES:
            return self._missing('individual_income_range', rule, 'Income range is invalid')
        user_income = profile.get_income_value()
        required = self._nonnegative_integer_value(rule)
        if required is None:
            return self._configuration_error(rule, 'invalid_individual_income')
        passed = user_income <= required
        return RuleResult(
            rule_type='max_individual_income', passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or f'Annual income up to ₹{required:,}',
            user_value=profile.individual_income_range,
            required_value=f'<= ₹{required:,}',
        )

    def _check_max_family_income(self, rule, profile):
        if not profile.family_income_range:
            return self._missing('family_income_range', rule, 'Family income not provided')
        if profile.family_income_range not in UserProfile.INCOME_VALUES:
            return self._missing('family_income_range', rule, 'Family income range is invalid')
        user_income = profile.get_family_income_value()
        required = self._nonnegative_integer_value(rule)
        if required is None:
            return self._configuration_error(rule, 'invalid_family_income')
        passed = user_income <= required
        return RuleResult(
            rule_type='max_family_income', passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or f'Family income up to ₹{required:,}',
        )

    def _check_education_min(self, rule, profile):
        if not profile.education_level:
            return self._missing('education_level', rule, 'Education level not provided')
        if profile.education_level not in EDUCATION_ORDER or rule.value not in EDUCATION_ORDER:
            return self._configuration_error(rule, 'invalid_education_min')
        user_level = EDUCATION_ORDER[profile.education_level]
        required_level = EDUCATION_ORDER[rule.value]
        passed = user_level >= required_level
        return RuleResult(
            rule_type='education_min', passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or f'Minimum education: {rule.value}',
        )

    def _check_education_max(self, rule, profile):
        if not profile.education_level:
            return self._missing('education_level', rule, 'Education level not provided')
        if profile.education_level not in EDUCATION_ORDER or rule.value not in EDUCATION_ORDER:
            return self._configuration_error(rule, 'invalid_education_max')
        user_level = EDUCATION_ORDER[profile.education_level]
        required_level = EDUCATION_ORDER[rule.value]
        passed = user_level <= required_level
        return RuleResult(
            rule_type='education_max', passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or f'Education up to {rule.value}',
        )

    def _check_employment_status(self, rule, profile):
        allowed_values = {value for value, _label in UserProfile.EMPLOYMENT_CHOICES}
        allowed = [value.strip() for value in rule.value.split(',') if value.strip()]
        if not allowed or not set(allowed).issubset(allowed_values):
            return self._configuration_error(rule, 'invalid_employment_value')
        if not profile.employment_status:
            return self._missing('employment_status', rule, 'Employment status not provided')
        passed = profile.employment_status in allowed
        return RuleResult(
            rule_type='employment_status', passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or 'Employment status',
            user_value=profile.employment_status,
            required_value=', '.join(allowed),
        )

    def _check_is_farmer(self, rule, profile):
        return self._check_boolean_flag('is_farmer', profile.is_farmer, rule, 'Must be a farmer')

    def _check_is_student(self, rule, profile):
        return self._check_boolean_flag('is_student', profile.is_student, rule, 'Must be a student')

    def _check_has_disability(self, rule, profile):
        return self._check_boolean_flag('has_disability', profile.has_disability, rule, 'Must have a disability')

    def _check_is_senior(self, rule, profile):
        return self._check_boolean_flag('is_senior_citizen', profile.is_senior_citizen, rule, 'Must be a senior citizen')

    def _check_is_widow(self, rule, profile):
        return self._check_boolean_flag('is_widow', profile.is_widow, rule, 'Must be a widow')

    def _check_is_rural(self, rule, profile):
        return self._check_boolean_flag('is_rural', profile.is_rural, rule, 'Must be from a rural area')

    def _check_is_job_seeker(self, rule, profile):
        return self._check_boolean_flag('is_job_seeker', profile.is_job_seeker, rule, 'Must be seeking employment')

    def _check_is_entrepreneur(self, rule, profile):
        return self._check_boolean_flag('is_entrepreneur', profile.is_entrepreneur, rule, 'Must be an entrepreneur')

    def _check_is_shg_member(self, rule, profile):
        return self._check_boolean_flag('is_shg_member', profile.is_shg_member, rule, 'Must be a SHG member')

    def _check_category(self, rule, profile):
        allowed_values = {value for value, _label in UserProfile.CATEGORY_CHOICES}
        allowed = [value.strip() for value in rule.value.split(',') if value.strip()]
        if not allowed or not set(allowed).issubset(allowed_values):
            return self._configuration_error(rule, 'invalid_category_value')
        if not profile.category:
            return self._missing('category', rule, 'Category not provided')
        passed = profile.category in allowed
        return RuleResult(
            rule_type='category', passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or 'Social category',
            user_value=profile.category,
            required_value=', '.join(allowed),
        )

    def _check_land_holding(self, rule, profile):
        allowed_values = {value for value, _label in UserProfile.LAND_CHOICES}
        allowed = [value.strip() for value in rule.value.split(',') if value.strip()]
        if not allowed or not set(allowed).issubset(allowed_values):
            return self._configuration_error(rule, 'invalid_land_holding_value')
        if not profile.land_holding:
            return self._missing('land_holding', rule, 'Land holding not provided')
        passed = profile.land_holding in allowed
        return RuleResult(
            rule_type='land_holding', passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or 'Land holding',
        )

    def _check_marital_status(self, rule, profile):
        allowed_values = {value for value, _label in UserProfile.MARITAL_CHOICES}
        allowed = [value.strip() for value in rule.value.split(',') if value.strip()]
        if not allowed or not set(allowed).issubset(allowed_values):
            return self._configuration_error(rule, 'invalid_marital_status_value')
        if not profile.marital_status:
            return self._missing('marital_status', rule, 'Marital status not provided')
        passed = profile.marital_status in allowed
        return RuleResult(
            rule_type='marital_status', passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or 'Marital status',
        )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _check_boolean_flag(self, field_name: str, user_value, rule: EligibilityRule, label: str) -> RuleResult:
        normalized = rule.value.strip().lower()
        if normalized not in ('true', '1', 'yes', 'false', '0', 'no'):
            return self._configuration_error(rule, 'invalid_boolean_value')
        if user_value is None:
            return self._missing(field_name, rule, f'{label} — not specified in profile')
        required = normalized in ('true', '1', 'yes')
        passed = user_value == required
        return RuleResult(
            rule_type=field_name, passed=passed,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or label,
            user_value='Yes' if user_value else 'No',
            required_value='Yes' if required else 'No',
        )

    def _missing(self, field_name: str, rule: EligibilityRule, reason: str) -> RuleResult:
        return RuleResult(
            rule_type=field_name,
            passed=False,
            is_mandatory=rule.is_mandatory,
            display_label=rule.display_label or field_name,
            reason='missing_info',
        )

    def _generate_summary(self, result: str, rule_results: list, missing_info: list) -> str:
        if result == UserSchemeMatch.RESULT_ELIGIBLE:
            return 'You appear to meet the currently configured eligibility conditions.'
        elif result == UserSchemeMatch.RESULT_INCOMPLETE:
            return f'Some information is missing from your profile ({len(missing_info)} field(s)) that may affect eligibility.'
        else:
            failed = [r for r in rule_results if not r.passed and r.is_mandatory]
            return f'You do not currently match {len(failed)} eligibility condition(s) for this scheme.'


# ─── Batch Re-evaluation ──────────────────────────────────────────────────────

def run_eligibility_for_user(user):
    """
    Re-evaluate all active schemes for a single user.
    Called when profile is updated or new schemes are added.
    """
    from apps.schemes.models import Scheme

    try:
        profile = user.profile
    except Exception:
        logger.warning(f"User {user.id} has no profile — skipping eligibility run.")
        return

    engine = EligibilityEngine()
    schemes = Scheme.objects.filter(
        status=Scheme.STATUS_ACTIVE,
        current_version__isnull=False,
        current_version__review_status='approved',
    ).select_related('current_version', 'state').prefetch_related('current_version__eligibility_rules')

    results = []
    for scheme in schemes:
        try:
            match = engine.evaluate_and_save(user, profile, scheme)
            results.append(match)
        except Exception as e:
            logger.error(f"Error evaluating scheme {scheme.id} for user {user.id}: {e}")

    from django.utils import timezone
    profile.last_eligibility_run = timezone.now()
    profile.save(update_fields=['last_eligibility_run'])
    return results
