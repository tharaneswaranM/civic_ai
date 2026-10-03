"""
Civic AI — Applications Tracker Model
Manual application tracking — we do NOT claim to integrate with government systems.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class ApplicationTracker(models.Model):
    """User-maintained record of a scheme application."""

    STATUS_NOT_STARTED = 'not_started'
    STATUS_PREPARING = 'preparing_documents'
    STATUS_READY = 'ready_to_apply'
    STATUS_SUBMITTED = 'submitted'
    STATUS_VERIFYING = 'under_verification'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_NOT_STARTED, _('Not Started')),
        (STATUS_PREPARING, _('Preparing Documents')),
        (STATUS_READY, _('Ready to Apply')),
        (STATUS_SUBMITTED, _('Submitted')),
        (STATUS_VERIFYING, _('Under Verification')),
        (STATUS_APPROVED, _('Approved')),
        (STATUS_REJECTED, _('Rejected')),
        (STATUS_COMPLETED, _('Completed')),
    ]

    STATUS_COLORS = {
        STATUS_NOT_STARTED: 'gray',
        STATUS_PREPARING: 'orange',
        STATUS_READY: 'blue',
        STATUS_SUBMITTED: 'blue',
        STATUS_VERIFYING: 'yellow',
        STATUS_APPROVED: 'green',
        STATUS_REJECTED: 'red',
        STATUS_COMPLETED: 'green',
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    scheme = models.ForeignKey(
        'schemes.Scheme',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default=STATUS_NOT_STARTED
    )
    notes = models.TextField(blank=True, help_text='Personal notes about this application')
    application_reference = models.CharField(
        max_length=200, blank=True,
        help_text='Application reference number from government portal (user-entered)'
    )
    submitted_date = models.DateField(null=True, blank=True)
    expected_decision_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('application tracker')
        verbose_name_plural = _('application trackers')
        unique_together = [['user', 'scheme']]
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user} → {self.scheme.name} [{self.status}]"

    def get_status_color(self):
        return self.STATUS_COLORS.get(self.status, 'gray')


class ApplicationNote(models.Model):
    """Timeline notes/updates for an application."""
    application = models.ForeignKey(
        ApplicationTracker, on_delete=models.CASCADE, related_name='timeline'
    )
    note = models.TextField()
    previous_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note on {self.application}"
