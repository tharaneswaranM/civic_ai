"""Small helpers for validating URLs stored in application data."""
from urllib.parse import urlsplit

from django.utils.http import url_has_allowed_host_and_scheme


def safe_external_https_url(value):
    """Return a stored external URL only when it is a well-formed HTTPS URL."""
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or '\\' in value
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        return ''
    try:
        parsed = urlsplit(value)
        parsed.port  # Force validation of the optional port.
    except ValueError:
        return ''
    if parsed.scheme.lower() != 'https' or not parsed.hostname:
        return ''
    if parsed.username or parsed.password:
        return ''
    return value


def safe_action_url(value, request):
    """Allow same-site paths or validated HTTPS links for notification actions."""
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        return ''
    if value.startswith('/') and not value.startswith('//') and '\\' not in value:
        if url_has_allowed_host_and_scheme(
            value,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return value
        return ''
    return safe_external_https_url(value)
