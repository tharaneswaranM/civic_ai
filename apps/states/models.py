"""
Civic AI — States Models
Configurable state and language data — no hardcoding.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


WEBP_IMAGE_DERIVATIVES = {
    'images/civic_ai/brand/cloud_bg.png': 'images/civic_ai/brand/cloud_bg.webp',
    'images/civic_ai/brand/hero_family.png': 'images/civic_ai/brand/hero_family.webp',
    'images/civic_ai/states/ap_state.png': 'images/civic_ai/states/ap_state.webp',
    'images/civic_ai/states/tn_state.png': 'images/civic_ai/states/tn_state.webp',
    'images/civic_ai/states/ap_transition.png': 'images/civic_ai/states/ap_transition.webp',
    'images/civic_ai/states/tn_transition.png': 'images/civic_ai/states/tn_transition.webp',
    'images/civic_ai/states/ap_login.png': 'images/civic_ai/states/ap_login.webp',
    'images/civic_ai/states/tn_login.png': 'images/civic_ai/states/tn_login.webp',
}


def webp_derivative(image_path):
    """Return a WebP path only for derivatives that ship with this project."""
    return WEBP_IMAGE_DERIVATIVES.get(image_path, '')


class Language(models.Model):
    """
    Supported languages. Adding a new language is purely a data operation.
    """
    code = models.CharField(max_length=10, unique=True)  # e.g. 'en', 'ta', 'te'
    name = models.CharField(max_length=50)               # English name: Tamil
    native_name = models.CharField(max_length=50)        # Native: தமிழ்
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    flag_emoji = models.CharField(max_length=10, blank=True)

    class Meta:
        verbose_name = _('language')
        verbose_name_plural = _('languages')
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class State(models.Model):
    """
    Indian state configuration.
    Adding a new state is purely a data + translation operation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True)   # e.g. 'AP', 'TN'
    name = models.CharField(max_length=100)               # Andhra Pradesh
    native_name = models.CharField(max_length=100)        # ఆంధ్ర ప్రదేశ్
    slug = models.SlugField(unique=True)                  # andhra-pradesh
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    # Supported languages for this state
    languages = models.ManyToManyField(
        Language,
        related_name='states',
        verbose_name=_('supported languages')
    )

    # ── State transition content ─────────────────────────────────────────────
    # These fields power the post-selection transition UX.
    # Adding a new state only needs these fields filled in.
    transition_title = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("e.g. 'Welcome to Andhra Pradesh'")
    )
    transition_subtitle = models.TextField(
        blank=True,
        help_text=_('Short welcoming description shown during state transition')
    )
    transition_image_url = models.CharField(
        max_length=500,
        blank=True,
        help_text=_('Path to primary transition hero image (relative to /static/)')
    )
    transition_secondary_image_url = models.CharField(
        max_length=500,
        blank=True,
        help_text=_('Optional secondary decorative image')
    )
    transition_color_primary = models.CharField(
        max_length=20,
        default='#1a56a4',
        help_text=_('Primary brand color for the state transition overlay')
    )
    transition_color_accent = models.CharField(
        max_length=20,
        default='#e8a020',
        help_text=_('Accent color for the state transition')
    )
    transition_landmark = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Name of the landmark shown (for alt text / accessibility)')
    )

    # Meta
    capital = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)  # e.g. South India

    # Scheme-related metadata
    scheme_count = models.PositiveIntegerField(default=0)
    last_scheme_update = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('state')
        verbose_name_plural = _('states')
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def get_primary_language(self):
        """Returns the first supported language for this state."""
        return self.languages.filter(is_active=True).first()

    @property
    def card_image(self):
        """Image for state selection card."""
        if self.code == 'AP':
            return 'images/civic_ai/states/ap_state.png'
        elif self.code == 'TN':
            return 'images/civic_ai/states/tn_state.png'
        return self.transition_image_url or 'images/civic_ai/brand/cloud_bg.png'

    @property
    def card_image_webp(self):
        return webp_derivative(self.card_image)

    @property
    def transition_image(self):
        """Hero visual for state transition welcome."""
        if self.transition_image_url and 'civic_ai' in self.transition_image_url:
            return self.transition_image_url
        if self.code == 'AP':
            return 'images/civic_ai/states/ap_transition.png'
        elif self.code == 'TN':
            return 'images/civic_ai/states/tn_transition.png'
        return self.transition_image_url or 'images/civic_ai/brand/cloud_bg.png'

    @property
    def transition_image_webp(self):
        return webp_derivative(self.transition_image)

    @property
    def login_image(self):
        """State-specific hero visual for login and onboarding."""
        if self.transition_secondary_image_url and 'civic_ai' in self.transition_secondary_image_url:
            return self.transition_secondary_image_url
        if self.code == 'AP':
            return 'images/civic_ai/states/ap_login.png'
        elif self.code == 'TN':
            return 'images/civic_ai/states/tn_login.png'
        return 'images/civic_ai/brand/hero_family.png'

    @property
    def login_image_webp(self):
        return webp_derivative(self.login_image)


class District(models.Model):
    """Districts within a state."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(
        State, on_delete=models.CASCADE, related_name='districts'
    )
    name = models.CharField(max_length=100)
    native_name = models.CharField(max_length=100, blank=True)
    code = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('district')
        verbose_name_plural = _('districts')
        ordering = ['state', 'name']
        unique_together = [['state', 'name']]

    def __str__(self):
        return f"{self.name}, {self.state.name}"
