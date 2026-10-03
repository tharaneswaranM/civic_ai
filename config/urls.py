"""
Civic AI — URL Configuration
Root URL dispatcher.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from apps.states.views import landing_page

urlpatterns = [
    # Root landing (ensures GET / always resolves)
    path('', landing_page, name='root_landing'),

    # Admin
    path('admin/', admin.site.urls),

    # i18n language switching
    path('i18n/', include('django.conf.urls.i18n')),

    # API endpoints (non-localized)
    path('api/', include([
        path('auth/', include('apps.accounts.api_urls', namespace='api_auth')),
        path('states/', include('apps.states.api_urls', namespace='api_states')),
        path('schemes/', include('apps.schemes.api_urls', namespace='api_schemes')),
        path('notifications/', include('apps.notifications.api_urls', namespace='api_notifications')),
        path('assistant/', include('apps.assistant.api_urls', namespace='api_assistant')),
    ])),
]

# i18n-prefixed URL patterns for the main web interface
urlpatterns += i18n_patterns(
    # Home alias
    path('', landing_page, name='home'),

    # Public pages
    path('', include('apps.states.urls', namespace='states')),

    # Authentication
    path('auth/', include('apps.accounts.urls', namespace='accounts')),

    # Authenticated app
    path('dashboard/', include('apps.profiles.urls', namespace='dashboard')),
    path('schemes/', include('apps.schemes.urls', namespace='schemes')),
    path('assistant/', include('apps.assistant.urls', namespace='assistant')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('applications/', include('apps.applications_tracker.urls', namespace='applications')),
    path('documents/', include('apps.documents.urls', namespace='documents')),

    prefix_default_language=False,
)

# Serve media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
