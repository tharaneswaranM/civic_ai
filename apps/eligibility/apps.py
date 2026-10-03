from django.apps import AppConfig


class EligibilityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.eligibility'
    verbose_name = 'Eligibility Engine'


class AssistantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assistant'
    verbose_name = 'AI Assistant'


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'Notifications'


class ApplicationsTrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.applications_tracker'
    verbose_name = 'Application Tracker'


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'
    verbose_name = 'Documents'


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'
    verbose_name = 'Audit Logs'
