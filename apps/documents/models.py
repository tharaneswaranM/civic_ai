"""
Civic AI — Documents Models (Phase 1: Metadata/Checklist only)
Full document storage implemented in Phase 5 with encryption.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class DocumentChecklist(models.Model):
    """Tracks which documents a user has for a specific scheme."""

    STATUS_AVAILABLE = 'available'
    STATUS_MISSING = 'missing'
    STATUS_PENDING = 'pending'

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, _('Available')),
        (STATUS_MISSING, _('Missing')),
        (STATUS_PENDING, _('Getting it')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='document_checklist'
    )
    scheme = models.ForeignKey(
        'schemes.Scheme',
        on_delete=models.CASCADE,
        related_name='user_documents'
    )
    document_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_MISSING)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('document checklist item')
        verbose_name_plural = _('document checklist items')
        ordering = ['scheme', 'document_name']

    def __str__(self):
        return f"{self.document_name} [{self.status}]"
