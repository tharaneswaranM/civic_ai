"""
Civic AI — States Views
Landing page, state selection, state transition, language selection.
All data-driven — no state-specific logic in views.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import translation
from django.urls import translate_url
from django.utils.http import url_has_allowed_host_and_scheme
from .language_settings import STATE_SUGGESTED_LANGUAGE
from .models import State, Language

logger = logging.getLogger(__name__)


def landing_page(request):
    """Public landing page."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    active_states = State.objects.filter(is_active=True).prefetch_related('languages')
    context = {
        'active_states': active_states,
        'page_title': _('Civic AI — Your Guide to Government Schemes'),
    }
    return render(request, 'public/landing.html', context)


def select_state(request):
    """State selection page."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    active_states = State.objects.filter(is_active=True).order_by('display_order')
    context = {
        'states': active_states,
        'page_title': _('Choose Your State'),
    }
    return render(request, 'states/select_state.html', context)


@require_POST
def set_state(request):
    """Save selected state to session and redirect to transition."""
    state_slug = request.POST.get('state_slug', '').strip()
    if not state_slug:
        return redirect('states:select_state')

    try:
        state = State.objects.get(slug=state_slug, is_active=True)
        request.session['selected_state'] = state.slug
        request.session['selected_state_name'] = state.name
        request.session['selected_state_code'] = state.code

        supported_languages = {code for code, _name in settings.LANGUAGES}
        selected_language = request.session.get('selected_language')
        if selected_language not in supported_languages:
            selected_language = STATE_SUGGESTED_LANGUAGE.get(
                state.code, settings.LANGUAGE_CODE
            )
            if selected_language not in supported_languages:
                selected_language = settings.LANGUAGE_CODE
            request.session['selected_language'] = selected_language
        translation.activate(selected_language)
        request.LANGUAGE_CODE = selected_language

        if request.user.is_authenticated:
            request.user.preferred_state = state
            request.user.save(update_fields=['preferred_state'])

        return redirect('states:state_transition', slug=state_slug)
    except State.DoesNotExist:
        return redirect('states:select_state')


def state_transition(request, slug):
    """State-specific transition/welcome animation page."""
    state = get_object_or_404(State, slug=slug, is_active=True)
    languages = Language.objects.filter(
        is_active=True,
        code__in=[code for code, _name in settings.LANGUAGES],
    ).order_by('display_order')
    suggested_language = STATE_SUGGESTED_LANGUAGE.get(state.code, settings.LANGUAGE_CODE)
    localized_title = state.transition_title or state.name
    localized_subtitle = state.transition_subtitle
    if state.code == 'AP' and state.transition_title == 'Welcome to Andhra Pradesh':
        localized_title = _('Welcome to Andhra Pradesh')
    elif state.code == 'TN' and state.transition_title == 'Welcome to Tamil Nadu':
        localized_title = _('Welcome to Tamil Nadu')
    if state.transition_subtitle == 'Government schemes and citizen services personalized for you.':
        localized_subtitle = _('Government schemes and citizen services personalized for you.')

    context = {
        'state': state,
        'languages': languages,
        'suggested_language': suggested_language,
        'localized_transition_title': localized_title,
        'localized_transition_subtitle': localized_subtitle or _('Government schemes and citizen services personalized for you.'),
        'page_title': localized_title,
    }
    return render(request, 'states/state_transition.html', context)


def select_language(request):
    """Language selection page."""
    languages = Language.objects.filter(
        is_active=True,
        code__in=[code for code, _name in settings.LANGUAGES],
    ).order_by('display_order')

    context = {
        'languages': languages,
        'page_title': _('Choose Your Language'),
    }
    return render(request, 'states/select_language.html', context)


@require_POST
def set_language(request):
    """Save selected language and redirect to login."""
    language_code = request.POST.get('language_code', 'en').strip()
    valid_codes = {code for code, _name in settings.LANGUAGES}

    if language_code not in valid_codes:
        language_code = 'en'

    request.session['selected_language'] = language_code

    if request.user.is_authenticated:
        request.user.preferred_language = language_code
        request.user.save(update_fields=['preferred_language'])

    translation.activate(language_code)
    request.LANGUAGE_CODE = language_code
    next_url = request.POST.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        response = redirect(translate_url(next_url, language_code))
    else:
        response = redirect('accounts:login')
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language_code,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )
    return response


# ─── API endpoints ────────────────────────────────────────────────────────────

def states_api(request):
    """JSON API: list of active states."""
    states = State.objects.filter(is_active=True).values(
        'id', 'code', 'name', 'native_name', 'slug',
        'transition_title', 'transition_subtitle',
        'transition_image_url', 'transition_color_primary',
        'transition_landmark',
    ).order_by('display_order')
    return JsonResponse({'states': list(states)})


def languages_api(request):
    """JSON API: list of active languages (optionally filtered by state)."""
    state_slug = request.GET.get('state')
    queryset = Language.objects.filter(is_active=True)

    if state_slug:
        queryset = queryset.filter(states__slug=state_slug)

    languages = queryset.values('code', 'name', 'native_name', 'flag_emoji').order_by('display_order')
    return JsonResponse({'languages': list(languages)})
