"""
Civic AI — User Profiles Model
Collects eligibility-relevant profile data in a privacy-conscious, consent-based manner.
"""
import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    """
    Extended profile for scheme eligibility matching.
    Separate from the User model to maintain clean auth/profile separation.
    """

    # ── Gender ───────────────────────────────────────────────────────────────
    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'
    GENDER_OTHER = 'other'
    GENDER_PREFER_NOT = 'prefer_not_to_say'

    GENDER_CHOICES = [
        (GENDER_MALE, _('Male')),
        (GENDER_FEMALE, _('Female')),
        (GENDER_OTHER, _('Other')),
        (GENDER_PREFER_NOT, _('Prefer not to say')),
    ]

    # ── Education ────────────────────────────────────────────────────────────
    EDUCATION_NO_FORMAL = 'no_formal'
    EDUCATION_PRIMARY = 'primary'
    EDUCATION_MIDDLE = 'middle'
    EDUCATION_SECONDARY = 'secondary'
    EDUCATION_HIGHER_SECONDARY = 'higher_secondary'
    EDUCATION_DIPLOMA = 'diploma'
    EDUCATION_GRADUATE = 'graduate'
    EDUCATION_POSTGRADUATE = 'postgraduate'
    EDUCATION_DOCTORATE = 'doctorate'

    EDUCATION_CHOICES = [
        (EDUCATION_NO_FORMAL, _('No Formal Education')),
        (EDUCATION_PRIMARY, _('Primary (up to Class 5)')),
        (EDUCATION_MIDDLE, _('Middle School (Class 6-8)')),
        (EDUCATION_SECONDARY, _('Secondary (Class 10)')),
        (EDUCATION_HIGHER_SECONDARY, _('Higher Secondary (Class 12)')),
        (EDUCATION_DIPLOMA, _('Diploma / ITI')),
        (EDUCATION_GRADUATE, _('Graduate (UG Degree)')),
        (EDUCATION_POSTGRADUATE, _('Postgraduate (PG Degree)')),
        (EDUCATION_DOCTORATE, _('Doctorate (PhD)')),
    ]

    # ── Employment ───────────────────────────────────────────────────────────
    EMPLOYMENT_EMPLOYED = 'employed'
    EMPLOYMENT_SELF_EMPLOYED = 'self_employed'
    EMPLOYMENT_UNEMPLOYED = 'unemployed'
    EMPLOYMENT_STUDENT = 'student'
    EMPLOYMENT_HOMEMAKER = 'homemaker'
    EMPLOYMENT_RETIRED = 'retired'
    EMPLOYMENT_FARMER = 'farmer'
    EMPLOYMENT_DAILY_WAGE = 'daily_wage'

    EMPLOYMENT_CHOICES = [
        (EMPLOYMENT_EMPLOYED, _('Employed (Salaried)')),
        (EMPLOYMENT_SELF_EMPLOYED, _('Self-Employed / Business')),
        (EMPLOYMENT_UNEMPLOYED, _('Unemployed / Job Seeker')),
        (EMPLOYMENT_STUDENT, _('Student')),
        (EMPLOYMENT_HOMEMAKER, _('Homemaker')),
        (EMPLOYMENT_RETIRED, _('Retired')),
        (EMPLOYMENT_FARMER, _('Farmer / Agricultural Worker')),
        (EMPLOYMENT_DAILY_WAGE, _('Daily Wage Worker')),
    ]

    # ── Income Ranges ────────────────────────────────────────────────────────
    INCOME_BELOW_1L = 'below_1l'
    INCOME_1L_2_5L = '1l_2_5l'
    INCOME_2_5L_5L = '2_5l_5l'
    INCOME_5L_8L = '5l_8l'
    INCOME_8L_12L = '8l_12l'
    INCOME_ABOVE_12L = 'above_12l'

    INCOME_CHOICES = [
        (INCOME_BELOW_1L, _('Below ₹1,00,000')),
        (INCOME_1L_2_5L, _('₹1,00,000 – ₹2,50,000')),
        (INCOME_2_5L_5L, _('₹2,50,000 – ₹5,00,000')),
        (INCOME_5L_8L, _('₹5,00,000 – ₹8,00,000')),
        (INCOME_8L_12L, _('₹8,00,000 – ₹12,00,000')),
        (INCOME_ABOVE_12L, _('Above ₹12,00,000')),
    ]

    INCOME_VALUES = {
        INCOME_BELOW_1L: 100000,
        INCOME_1L_2_5L: 250000,
        INCOME_2_5L_5L: 500000,
        INCOME_5L_8L: 800000,
        INCOME_8L_12L: 1200000,
        INCOME_ABOVE_12L: 9999999,
    }

    # ── Marital Status ───────────────────────────────────────────────────────
    MARITAL_SINGLE = 'single'
    MARITAL_MARRIED = 'married'
    MARITAL_WIDOWED = 'widowed'
    MARITAL_DIVORCED = 'divorced'
    MARITAL_SEPARATED = 'separated'

    MARITAL_CHOICES = [
        (MARITAL_SINGLE, _('Single')),
        (MARITAL_MARRIED, _('Married')),
        (MARITAL_WIDOWED, _('Widowed')),
        (MARITAL_DIVORCED, _('Divorced')),
        (MARITAL_SEPARATED, _('Separated')),
    ]

    # ── Category (Caste) ─────────────────────────────────────────────────────
    CATEGORY_GENERAL = 'general'
    CATEGORY_OBC = 'obc'
    CATEGORY_SC = 'sc'
    CATEGORY_ST = 'st'
    CATEGORY_EWS = 'ews'

    CATEGORY_CHOICES = [
        (CATEGORY_GENERAL, _('General')),
        (CATEGORY_OBC, _('OBC (Other Backward Class)')),
        (CATEGORY_SC, _('SC (Scheduled Caste)')),
        (CATEGORY_ST, _('ST (Scheduled Tribe)')),
        (CATEGORY_EWS, _('EWS (Economically Weaker Section)')),
    ]

    # ── Land Holding ─────────────────────────────────────────────────────────
    LAND_LANDLESS = 'landless'
    LAND_MARGINAL = 'marginal'     # < 1 hectare
    LAND_SMALL = 'small'           # 1-2 hectares
    LAND_MEDIUM = 'medium'         # 2-4 hectares
    LAND_LARGE = 'large'           # > 4 hectares

    LAND_CHOICES = [
        (LAND_LANDLESS, _('Landless')),
        (LAND_MARGINAL, _('Marginal (less than 1 hectare)')),
        (LAND_SMALL, _('Small (1–2 hectares)')),
        (LAND_MEDIUM, _('Medium (2–4 hectares)')),
        (LAND_LARGE, _('Large (more than 4 hectares)')),
    ]

    # ─────────────────────────────────────────────────────────────────────────

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # ── Personal ─────────────────────────────────────────────────────────────
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    age = models.PositiveSmallIntegerField(
        _('age'), null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(150)]
    )
    gender = models.CharField(
        _('gender'), max_length=20,
        choices=GENDER_CHOICES, blank=True
    )

    # ── Location ─────────────────────────────────────────────────────────────
    state = models.ForeignKey(
        'states.State',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='profile_users',
        verbose_name=_('state')
    )
    district = models.ForeignKey(
        'states.District',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='profile_users',
        verbose_name=_('district')
    )
    city_village = models.CharField(_('city / village'), max_length=200, blank=True)
    pin_code = models.CharField(_('PIN code'), max_length=10, blank=True)
    is_rural = models.BooleanField(_('rural area'), null=True, blank=True)

    # ── Education ────────────────────────────────────────────────────────────
    education_level = models.CharField(
        _('education level'), max_length=30,
        choices=EDUCATION_CHOICES, blank=True
    )
    is_student = models.BooleanField(_('currently a student'), null=True, blank=True)
    student_course = models.CharField(_('course / programme'), max_length=200, blank=True)
    institution_type = models.CharField(
        _('institution type'), max_length=100, blank=True,
        help_text=_('e.g. Government, Private, Aided')
    )

    # ── Employment ───────────────────────────────────────────────────────────
    employment_status = models.CharField(
        _('employment status'), max_length=30,
        choices=EMPLOYMENT_CHOICES, blank=True
    )
    occupation = models.CharField(_('occupation'), max_length=200, blank=True)
    sector = models.CharField(
        _('sector'), max_length=100, blank=True,
        help_text=_('e.g. Agriculture, IT, Manufacturing, Healthcare')
    )

    # ── Income ───────────────────────────────────────────────────────────────
    individual_income_range = models.CharField(
        _('individual annual income'), max_length=20,
        choices=INCOME_CHOICES, blank=True
    )
    family_income_range = models.CharField(
        _('family annual income'), max_length=20,
        choices=INCOME_CHOICES, blank=True
    )

    # ── Family ───────────────────────────────────────────────────────────────
    marital_status = models.CharField(
        _('marital status'), max_length=20,
        choices=MARITAL_CHOICES, blank=True
    )
    number_of_dependents = models.PositiveSmallIntegerField(
        _('number of dependents'), null=True, blank=True
    )

    # ── Category (Sensitive — collected with consent) ─────────────────────
    category = models.CharField(
        _('social category'), max_length=20,
        choices=CATEGORY_CHOICES, blank=True
    )

    # ── Scheme-Relevant Flags ────────────────────────────────────────────────
    is_farmer = models.BooleanField(_('is a farmer'), null=True, blank=True)
    land_holding = models.CharField(
        _('land holding'), max_length=20,
        choices=LAND_CHOICES, blank=True
    )
    has_disability = models.BooleanField(_('has a disability'), null=True, blank=True)
    disability_type = models.CharField(_('disability type'), max_length=200, blank=True)
    is_senior_citizen = models.BooleanField(_('senior citizen (60+)'), null=True, blank=True)
    is_widow = models.BooleanField(_('widow'), null=True, blank=True)
    is_shg_member = models.BooleanField(_('SHG member'), null=True, blank=True)
    is_ration_card_holder = models.BooleanField(_('ration card holder'), null=True, blank=True)
    ration_card_type = models.CharField(
        _('ration card type'), max_length=50, blank=True,
        help_text=_('e.g. APL, BPL, AAY, NPHH')
    )
    is_entrepreneur = models.BooleanField(_('entrepreneur / startup founder'), null=True, blank=True)
    is_job_seeker = models.BooleanField(_('actively seeking employment'), null=True, blank=True)

    # ── Completion tracking ──────────────────────────────────────────────────
    completion_percentage = models.PositiveSmallIntegerField(default=0)
    last_eligibility_run = models.DateTimeField(null=True, blank=True)

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"Profile of {self.user}"

    def clean(self):
        super().clean()
        if self.district_id and not self.state_id:
            raise ValidationError({'district': _('Choose a state for this district.')})
        if self.district_id and self.state_id and self.district.state_id != self.state_id:
            raise ValidationError({'district': _('The district must belong to the selected state.')})

    def calculate_completion(self):
        """
        Calculate profile completion percentage.
        Returns int 0-100.
        """
        fields = [
            bool(self.user.full_name),
            bool(self.date_of_birth),
            bool(self.gender),
            bool(self.state),
            bool(self.district),
            bool(self.education_level),
            bool(self.employment_status),
            bool(self.individual_income_range),
            bool(self.family_income_range),
            bool(self.marital_status),
            bool(self.category),
        ]
        filled = sum(fields)
        return int((filled / len(fields)) * 100)

    def update_completion(self):
        self.completion_percentage = self.calculate_completion()
        self.save(update_fields=['completion_percentage', 'updated_at'])

    def get_income_value(self):
        """Returns the upper bound of the selected income range for comparisons."""
        return UserProfile.INCOME_VALUES.get(self.individual_income_range, 0)

    def get_family_income_value(self):
        return UserProfile.INCOME_VALUES.get(self.family_income_range, 0)
