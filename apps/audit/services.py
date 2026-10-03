"""
Civic AI — Audit Services
Utility functions for creating non-sensitive audit logs.
"""
import logging
from .models import AuditLog

logger = logging.getLogger(__name__)


def get_client_ip(request):
    if not request:
        return None
    # Use the socket peer by default. Trust forwarded headers only when a
    # deployment has a configured, trusted-proxy middleware in front of Django.
    return request.META.get('REMOTE_ADDR')


def log_audit_event(event, request=None, user=None, mobile_masked='', metadata=None):
    """
    Safely record an audit log event.
    Never throws exceptions that interrupt user workflows.
    Never logs sensitive PII, OTPs, or passwords.
    """
    try:
        if request and not user and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user

        ip = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''

        return AuditLog.objects.create(
            user=user,
            event=event,
            mobile_masked=mobile_masked or '',
            ip_address=ip,
            user_agent=user_agent,
            metadata=metadata or {},
        )
    except Exception:
        logger.exception("Failed to record audit event %s", event)
        return None
