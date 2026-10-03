"""
Civic AI — Accounts Models
Custom User model with mobile-number-based authentication.
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager for the custom User model."""

    def create_user(self, mobile_number, **extra_fields):
        if not mobile_number:
            raise ValueError(_('Mobile number is required'))
        user = self.model(mobile_number=mobile_number, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        user = self.model(mobile_number=mobile_number, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User with mobile number as the primary identifier.
    Authentication is done via OTP, not password.
    """

    LANGUAGE_ENGLISH = 'en'
    LANGUAGE_TAMIL = 'ta'
    LANGUAGE_TELUGU = 'te'

    LANGUAGE_CHOICES = [
        (LANGUAGE_ENGLISH, 'English'),
        (LANGUAGE_TAMIL, 'தமிழ்'),
        (LANGUAGE_TELUGU, 'తెలుగు'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mobile_number = models.CharField(
        _('mobile number'),
        max_length=15,
        unique=True,
        help_text=_('Enter with country code, e.g. +919876543210')
    )
    full_name = models.CharField(_('full name'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), blank=True)

    # Language preference
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default=LANGUAGE_ENGLISH
    )

    # State preference (FK set after states app is ready)
    preferred_state = models.ForeignKey(
        'states.State',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('preferred state')
    )

    # Account status
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_profile_complete = models.BooleanField(_('profile complete'), default=False)

    # Timestamps
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), null=True, blank=True)

    # Privacy & consent
    consent_data_processing = models.BooleanField(
        _('consent to data processing'), default=False
    )
    consent_date = models.DateTimeField(_('consent date'), null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'mobile_number'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    def __str__(self):
        return self.full_name or self.mobile_number

    def get_display_name(self):
        return self.full_name or self.mobile_number

    def get_short_name(self):
        if self.full_name:
            return self.full_name.split()[0]
        return self.mobile_number


class OTPRequest(models.Model):
    """
    Tracks OTP requests for authentication.
    OTPs are stored as hashed values.
    """

    PURPOSE_LOGIN = 'login'
    PURPOSE_REGISTER = 'register'
    PURPOSE_VERIFY = 'verify'

    PURPOSE_CHOICES = [
        (PURPOSE_LOGIN, 'Login'),
        (PURPOSE_REGISTER, 'Register'),
        (PURPOSE_VERIFY, 'Verify'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_VERIFIED = 'verified'
    STATUS_EXPIRED = 'expired'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mobile_number = models.CharField(max_length=15, db_index=True)
    otp_hash = models.CharField(max_length=255)  # Never store OTP plaintext
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default=PURPOSE_LOGIN)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('OTP request')
        verbose_name_plural = _('OTP requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mobile_number', 'status', 'created_at']),
        ]

    def __str__(self):
        return f"OTP for {self.mobile_number} [{self.status}]"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return self.status == self.STATUS_PENDING and not self.is_expired()
