"""Resolve one UI language for each request after session and auth loading."""
from django.conf import settings
from django.utils import translation
from apps.states.language_settings import STATE_SUGGESTED_LANGUAGE


class UserLanguageMiddleware:
    """Apply the account, explicit choice, state suggestion, then English."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        supported = {code for code, _name in settings.LANGUAGES}
        language = None

        if request.user.is_authenticated:
            candidate = request.user.preferred_language
            if candidate in supported:
                language = candidate

        if language is None:
            candidate = request.session.get('selected_language')
            if candidate in supported:
                language = candidate

        if language is None:
            candidate = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
            if candidate in supported:
                language = candidate

        if language is None:
            candidate = translation.get_language_from_path(request.path_info)
            if candidate in supported:
                language = candidate

        if language is None:
            candidate = STATE_SUGGESTED_LANGUAGE.get(
                request.session.get('selected_state_code')
            )
            if candidate in supported:
                language = candidate

        language = language or settings.LANGUAGE_CODE
        translation.activate(language)
        request.LANGUAGE_CODE = language
        return self.get_response(request)
