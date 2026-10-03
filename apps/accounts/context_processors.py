"""
Civic AI — Accounts Context Processors
"""


def user_language(request):
    """Inject current language into every template context."""
    lang = getattr(request, 'LANGUAGE_CODE', 'en')

    language_names = {
        'en': {'name': 'English', 'native': 'English', 'flag': '🇬🇧'},
        'ta': {'name': 'Tamil', 'native': 'தமிழ்', 'flag': '🇮🇳'},
        'te': {'name': 'Telugu', 'native': 'తెలుగు', 'flag': '🇮🇳'},
    }

    return {
        'current_language': lang,
        'current_language_info': language_names.get(lang, language_names['en']),
        'available_languages': language_names,
    }
