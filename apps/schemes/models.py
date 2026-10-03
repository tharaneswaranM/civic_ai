"""
Civic AI — Schemes Models
Full scheme data model with versioning, categories, eligibility rules, and translations.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class SchemeCategory(models.Model):
    """Categories for filtering/browsing schemes."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='Icon class or emoji')
    color = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='subcategories'
    )

    class Meta:
        verbose_name = _('scheme category')
        verbose_name_plural = _('scheme categories')
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class Department(models.Model):
    """Government department that administers schemes."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50, blank=True)
    state = models.ForeignKey(
        'states.State', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='departments',
        help_text='Null for central government departments'
    )
    website = models.URLField(blank=True)
    is_central = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('department')
        verbose_name_plural = _('departments')
        ordering = ['name']

    def __str__(self):
        return self.name


class Scheme(models.Model):
    """
    A government scheme.
    The scheme itself is the parent record; actual eligibility data lives in SchemeVersion.
    """

    LEVEL_CENTRAL = 'central'
    LEVEL_STATE = 'state'
    LEVEL_DISTRICT = 'district'

    LEVEL_CHOICES = [
        (LEVEL_CENTRAL, _('Central Government')),
        (LEVEL_STATE, _('State Government')),
        (LEVEL_DISTRICT, _('District Level')),
    ]

    STATUS_ACTIVE = 'active'
    STATUS_UPCOMING = 'upcoming'
    STATUS_CLOSED = 'closed'
    STATUS_SUSPENDED = 'suspended'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, _('Active')),
        (STATUS_UPCOMING, _('Upcoming')),
        (STATUS_CLOSED, _('Closed')),
        (STATUS_SUSPENDED, _('Temporarily Suspended')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('scheme name'), max_length=300)
    slug = models.SlugField(unique=True, max_length=300)
    short_name = models.CharField(max_length=100, blank=True)

    level = models.CharField(_('government level'), max_length=20, choices=LEVEL_CHOICES)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    state = models.ForeignKey(
        'states.State', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='schemes',
        help_text='Null for central schemes'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='schemes'
    )
    categories = models.ManyToManyField(
        SchemeCategory, related_name='schemes', blank=True
    )

    # Active version reference
    current_version = models.ForeignKey(
        'SchemeVersion', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='current_for_scheme'
    )

    # Discovery / featured
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)  # Flagged when just added
    new_since = models.DateField(null=True, blank=True)

    # Source tracking
    official_url = models.URLField(blank=True)
    official_source_name = models.CharField(max_length=200, blank=True)
    last_verified_date = models.DateField(null=True, blank=True)

    # Dates
    launch_date = models.DateField(null=True, blank=True)
    application_start_date = models.DateField(null=True, blank=True)
    application_end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('scheme')
        verbose_name_plural = _('schemes')
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['status', 'level']),
            models.Index(fields=['state', 'status']),
        ]

    def __str__(self):
        return self.name

    def is_closing_soon(self, days=7):
        if self.application_end_date:
            delta = self.application_end_date - timezone.now().date()
            return 0 <= delta.days <= days
        return False

    def get_description(self):
        if self.current_version:
            return self.current_version.description
        return ''

    def get_benefit(self):
        if self.current_version:
            return self.current_version.benefit_summary
        return ''


class SchemeVersion(models.Model):
    """
    Versioned snapshot of a scheme's details.
    When eligibility rules change, a new version is created rather than overwriting.
    """

    REVIEW_PENDING = 'pending'
    REVIEW_APPROVED = 'approved'
    REVIEW_REJECTED = 'rejected'

    REVIEW_CHOICES = [
        (REVIEW_PENDING, 'Pending Review'),
        (REVIEW_APPROVED, 'Approved'),
        (REVIEW_REJECTED, 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scheme = models.ForeignKey(
        Scheme, on_delete=models.CASCADE, related_name='versions'
    )
    version_number = models.PositiveSmallIntegerField(default=1)

    # Content
    description = models.TextField()
    benefit_summary = models.TextField()
    how_to_apply = models.TextField(blank=True)
    additional_info = models.TextField(blank=True)

    # Review
    review_status = models.CharField(max_length=20, choices=REVIEW_CHOICES, default=REVIEW_PENDING)
    reviewed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_versions'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    # Source
    source_url = models.URLField(blank=True)
    source_document = models.CharField(max_length=300, blank=True)
    source_date = models.DateField(null=True, blank=True)
    extracted_by_ai = models.BooleanField(default=False)

    effective_from = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_versions'
    )

    class Meta:
        verbose_name = _('scheme version')
        verbose_name_plural = _('scheme versions')
        ordering = ['scheme', '-version_number']
        unique_together = [['scheme', 'version_number']]

    def __str__(self):
        return f"{self.scheme.name} v{self.version_number}"


class EligibilityRule(models.Model):
    """
    Structured eligibility rule for a scheme version.
    The eligibility engine evaluates these deterministically against user profiles.
    """

    RULE_MIN_AGE = 'min_age'
    RULE_MAX_AGE = 'max_age'
    RULE_GENDER = 'gender'
    RULE_STATE = 'state'
    RULE_DISTRICT = 'district'
    RULE_MAX_INDIVIDUAL_INCOME = 'max_individual_income'
    RULE_MAX_FAMILY_INCOME = 'max_family_income'
    RULE_EDUCATION_MIN = 'education_min'
    RULE_EDUCATION_MAX = 'education_max'
    RULE_EMPLOYMENT_STATUS = 'employment_status'
    RULE_IS_FARMER = 'is_farmer'
    RULE_IS_STUDENT = 'is_student'
    RULE_HAS_DISABILITY = 'has_disability'
    RULE_IS_SENIOR = 'is_senior_citizen'
    RULE_IS_WIDOW = 'is_widow'
    RULE_CATEGORY = 'category'
    RULE_LAND_HOLDING = 'land_holding'
    RULE_MARITAL_STATUS = 'marital_status'
    RULE_IS_RURAL = 'is_rural'
    RULE_IS_JOB_SEEKER = 'is_job_seeker'
    RULE_IS_ENTREPRENEUR = 'is_entrepreneur'
    RULE_IS_SHG_MEMBER = 'is_shg_member'

    RULE_TYPE_CHOICES = [
        (RULE_MIN_AGE, 'Minimum Age'),
        (RULE_MAX_AGE, 'Maximum Age'),
        (RULE_GENDER, 'Gender Requirement'),
        (RULE_STATE, 'State'),
        (RULE_DISTRICT, 'District'),
        (RULE_MAX_INDIVIDUAL_INCOME, 'Max Individual Income'),
        (RULE_MAX_FAMILY_INCOME, 'Max Family Income'),
        (RULE_EDUCATION_MIN, 'Minimum Education'),
        (RULE_EDUCATION_MAX, 'Maximum Education'),
        (RULE_EMPLOYMENT_STATUS, 'Employment Status'),
        (RULE_IS_FARMER, 'Must be Farmer'),
        (RULE_IS_STUDENT, 'Must be Student'),
        (RULE_HAS_DISABILITY, 'Must have Disability'),
        (RULE_IS_SENIOR, 'Must be Senior Citizen'),
        (RULE_IS_WIDOW, 'Must be Widow'),
        (RULE_CATEGORY, 'Social Category'),
        (RULE_LAND_HOLDING, 'Land Holding'),
        (RULE_MARITAL_STATUS, 'Marital Status'),
        (RULE_IS_RURAL, 'Must be from Rural Area'),
        (RULE_IS_JOB_SEEKER, 'Must be Job Seeker'),
        (RULE_IS_ENTREPRENEUR, 'Must be Entrepreneur'),
        (RULE_IS_SHG_MEMBER, 'Must be SHG Member'),
    ]

    OPERATOR_EQ = 'eq'
    OPERATOR_GTE = 'gte'
    OPERATOR_LTE = 'lte'
    OPERATOR_IN = 'in'
    OPERATOR_BOOL = 'bool'

    OPERATOR_CHOICES = [
        (OPERATOR_EQ, '= Equal'),
        (OPERATOR_GTE, '>= Greater than or equal'),
        (OPERATOR_LTE, '<= Less than or equal'),
        (OPERATOR_IN, 'IN (one of list)'),
        (OPERATOR_BOOL, 'Boolean check'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scheme_version = models.ForeignKey(
        SchemeVersion, on_delete=models.CASCADE, related_name='eligibility_rules'
    )
    rule_type = models.CharField(max_length=50, choices=RULE_TYPE_CHOICES)
    operator = models.CharField(max_length=10, choices=OPERATOR_CHOICES, default=OPERATOR_EQ)
    value = models.CharField(max_length=500, help_text='Rule value. For IN operator, use comma-separated values')
    is_mandatory = models.BooleanField(
        default=True,
        help_text='If True, user MUST meet this rule. If False, it is advisory.'
    )
    display_label = models.CharField(
        max_length=200, blank=True,
        help_text='Human-readable label shown on scheme detail page'
    )
    notes = models.TextField(blank=True, help_text='Admin notes about this rule')

    class Meta:
        verbose_name = _('eligibility rule')
        verbose_name_plural = _('eligibility rules')
        ordering = ['scheme_version', 'rule_type']

    def __str__(self):
        return f"{self.rule_type} {self.operator} {self.value}"


class RequiredDocument(models.Model):
    """Documents a user must provide to apply for a scheme."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scheme_version = models.ForeignKey(
        SchemeVersion, on_delete=models.CASCADE, related_name='required_documents'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=True)
    alternatives = models.TextField(
        blank=True,
        help_text='Alternative documents that can be submitted instead'
    )
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = _('required document')
        verbose_name_plural = _('required documents')
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class SchemeTranslation(models.Model):
    """
    Translated content for a scheme version.
    Separate from Django's built-in i18n for scheme-specific content.
    """
    scheme_version = models.ForeignKey(
        SchemeVersion, on_delete=models.CASCADE, related_name='translations'
    )
    language = models.ForeignKey(
        'states.Language', on_delete=models.CASCADE, related_name='scheme_translations'
    )
    name = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    benefit_summary = models.TextField(blank=True)
    how_to_apply = models.TextField(blank=True)
    translated_by_ai = models.BooleanField(default=False)
    reviewed = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('scheme translation')
        verbose_name_plural = _('scheme translations')
        unique_together = [['scheme_version', 'language']]

    def __str__(self):
        return f"{self.scheme_version} [{self.language.code}]"


class UserSchemeMatch(models.Model):
    """
    Result of running the eligibility engine for a user against a scheme.
    Recalculated when the user profile changes or the scheme version changes.
    """

    RESULT_ELIGIBLE = 'eligible'
    RESULT_INCOMPLETE = 'incomplete'
    RESULT_NOT_ELIGIBLE = 'not_eligible'

    RESULT_CHOICES = [
        (RESULT_ELIGIBLE, _('Likely Eligible')),
        (RESULT_INCOMPLETE, _('More Information Needed')),
        (RESULT_NOT_ELIGIBLE, _('Does Not Currently Match')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='scheme_matches'
    )
    scheme = models.ForeignKey(
        Scheme, on_delete=models.CASCADE, related_name='user_matches'
    )
    scheme_version = models.ForeignKey(
        SchemeVersion, on_delete=models.CASCADE, related_name='user_matches'
    )
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    matched_rules = models.JSONField(default=list)    # list of {rule_type, passed}
    missing_info = models.JSONField(default=list)     # profile fields missing
    evaluated_at = models.DateTimeField(auto_now=True)
    is_saved = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('user scheme match')
        verbose_name_plural = _('user scheme matches')
        unique_together = [['user', 'scheme']]
        ordering = ['-evaluated_at']
        indexes = [
            models.Index(fields=['user', 'result']),
            models.Index(fields=['user', '-evaluated_at']),
        ]

    def __str__(self):
        return f"{self.user} — {self.scheme.name} [{self.result}]"


class SavedScheme(models.Model):
    """User-bookmarked schemes."""
    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='saved_schemes'
    )
    scheme = models.ForeignKey(
        Scheme, on_delete=models.CASCADE, related_name='saved_by'
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'scheme']]
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user} saved {self.scheme.name}"
