"""
Civic AI — Assistant Models
Stores conversation history for the AI assistant.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class AssistantConversation(models.Model):
    """A conversation session with the AI assistant."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    title = models.CharField(max_length=300, blank=True)
    context_scheme = models.ForeignKey(
        'schemes.Scheme', on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text='Scheme this conversation is about (if any)'
    )
    language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('conversation')
        verbose_name_plural = _('conversations')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation {self.id} by {self.user}"


class AssistantMessage(models.Model):
    """A single message in an assistant conversation."""

    ROLE_USER = 'user'
    ROLE_ASSISTANT = 'assistant'
    ROLE_SYSTEM = 'system'

    ROLE_CHOICES = [
        (ROLE_USER, 'User'),
        (ROLE_ASSISTANT, 'Assistant'),
        (ROLE_SYSTEM, 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        AssistantConversation, on_delete=models.CASCADE, related_name='messages'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    sources = models.JSONField(default=list, help_text='RAG source citations')
    tokens_used = models.PositiveIntegerField(default=0)
    model_used = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        ordering = ['conversation', 'created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
