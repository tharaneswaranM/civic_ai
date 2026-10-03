"""
Civic AI — Audit Models
Tracks important system events without logging sensitive data.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    """System audit trail for security and compliance."""

    EVENT_LOGIN_SUCCESS = 'login_success'
    EVENT_LOGIN_FAILED = 'login_failed'
    EVENT_LOGOUT = 'logout'
    EVENT_OTP_SENT = 'otp_sent'
    EVENT_OTP_VERIFIED = 'otp_verified'
    EVENT_OTP_FAILED = 'otp_failed'
    EVENT_OTP_RATE_LIMITED = 'otp_rate_limited'
    EVENT_PROFILE_UPDATED = 'profile_updated'
    EVENT_SCHEME_VIEWED = 'scheme_viewed'
    EVENT_SCHEME_SAVED = 'scheme_saved'
    EVENT_APPLICATION_STATUS_CHANGED = 'application_status_changed'
    EVENT_DATA_EXPORTED = 'data_exported'
    EVENT_ACCOUNT_DELETED = 'account_deleted'
    EVENT_CONSENT_GIVEN = 'consent_given'
    EVENT_CONSENT_WITHDRAWN = 'consent_withdrawn'
    EVENT_AI_QUERY = 'ai_query'

    EVENT_CHOICES = [
        (EVENT_LOGIN_SUCCESS, 'Login Success'),
        (EVENT_LOGIN_FAILED, 'Login Failed'),
        (EVENT_LOGOUT, 'Logout'),
        (EVENT_OTP_SENT, 'OTP Sent'),
        (EVENT_OTP_VERIFIED, 'OTP Verified'),
        (EVENT_OTP_FAILED, 'OTP Failed'),
        (EVENT_OTP_RATE_LIMITED, 'OTP Rate Limited'),
        (EVENT_PROFILE_UPDATED, 'Profile Updated'),
        (EVENT_SCHEME_VIEWED, 'Scheme Viewed'),
        (EVENT_SCHEME_SAVED, 'Scheme Saved'),
        (EVENT_APPLICATION_STATUS_CHANGED, 'Application Status Changed'),
        (EVENT_DATA_EXPORTED, 'Data Exported'),
        (EVENT_ACCOUNT_DELETED, 'Account Deleted'),
        (EVENT_CONSENT_GIVEN, 'Consent Given'),
        (EVENT_CONSENT_WITHDRAWN, 'Consent Withdrawn'),
        (EVENT_AI_QUERY, 'AI Query'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_logs'
    )
    event = models.CharField(max_length=50, choices=EVENT_CHOICES)
    # Store mobile partially masked — never full number
    mobile_masked = models.CharField(max_length=15, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(
        default=dict,
        help_text='Non-sensitive context. Never store OTPs, passwords, or PII here.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.event} at {self.created_at}"
