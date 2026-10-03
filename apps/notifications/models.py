"""
Civic AI — Notifications Models
In-app notification system designed to support multiple channels later.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Notification(models.Model):
    """An in-app notification for a user."""

    TYPE_NEW_SCHEME = 'new_scheme'
    TYPE_ELIGIBILITY_CHANGED = 'eligibility_changed'
    TYPE_DEADLINE = 'deadline'
    TYPE_DOCUMENT_REQUIRED = 'document_required'
    TYPE_APPLICATION_UPDATE = 'application_update'
    TYPE_GENERAL = 'general'

    TYPE_CHOICES = [
        (TYPE_NEW_SCHEME, _('New Scheme')),
        (TYPE_ELIGIBILITY_CHANGED, _('Eligibility Changed')),
        (TYPE_DEADLINE, _('Deadline Reminder')),
        (TYPE_DOCUMENT_REQUIRED, _('Document Required')),
        (TYPE_APPLICATION_UPDATE, _('Application Update')),
        (TYPE_GENERAL, _('General')),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_NORMAL = 'normal'
    PRIORITY_HIGH = 'high'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_NORMAL, 'Normal'),
        (PRIORITY_HIGH, 'High'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    title = models.CharField(max_length=300)
    body = models.TextField()
    action_url = models.CharField(max_length=500, blank=True)
    action_label = models.CharField(max_length=100, blank=True)

    # Related objects
    scheme = models.ForeignKey(
        'schemes.Scheme', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='notifications'
    )

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"{self.notification_type}: {self.title}"


class NotificationPreference(models.Model):
    """User's preferences for notification delivery channels."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    in_app = models.BooleanField(default=True)
    email = models.BooleanField(default=False)
    sms = models.BooleanField(default=False)
    push = models.BooleanField(default=False)

    # Per-type preferences
    new_scheme_alerts = models.BooleanField(default=True)
    eligibility_change_alerts = models.BooleanField(default=True)
    deadline_reminders = models.BooleanField(default=True)
    application_updates = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('notification preference')
        verbose_name_plural = _('notification preferences')

    def __str__(self):
        return f"Notification prefs for {self.user}"
