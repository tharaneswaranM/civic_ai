"""
Civic AI — Django Settings
Modular, production-aware configuration using python-decouple.
"""

from pathlib import Path
from decouple import config, Csv

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ─────────────────────────────────────────────────────────────────
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='dev-insecure-key-change-me' if DEBUG else '')
if not SECRET_KEY:
    raise ValueError('SECRET_KEY must be set when DEBUG is False.')
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,testserver' if DEBUG else '',
    cast=Csv(),
)
if not DEBUG and not ALLOWED_HOSTS:
    raise ValueError('ALLOWED_HOSTS must be set when DEBUG is False.')

# ─── Applications ─────────────────────────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'rest_framework',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.profiles',
    'apps.states',
    'apps.schemes',
    'apps.eligibility',
    'apps.assistant',
    'apps.notifications',
    'apps.applications_tracker',
    'apps.documents',
    'apps.audit',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─── Middleware ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.accounts.middleware.UserLanguageMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# ─── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'apps.states.context_processors.active_states',
                'apps.accounts.context_processors.user_language',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ─── Database ─────────────────────────────────────────────────────────────────
USE_SQLITE = config('USE_SQLITE', default=DEBUG, cast=bool)
if not DEBUG and USE_SQLITE:
    raise ValueError('USE_SQLITE must be False when DEBUG is False.')

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    if not DEBUG:
        required_database_settings = ('DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST')
        missing_database_settings = [
            name for name in required_database_settings
            if not config(name, default='')
        ]
        if missing_database_settings:
            raise ValueError(
                'Production database settings are required: '
                + ', '.join(missing_database_settings)
            )
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='civicai_db'),
            'USER': config('DB_USER', default='civicai_user'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# ─── Caching ──────────────────────────────────────────────────────────────────
USE_REDIS = config('USE_REDIS', default=False, cast=bool)

if USE_REDIS:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': config('REDIS_URL', default='redis://localhost:6379/0'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# ─── Authentication ───────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ─── Internationalization ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', 'English'),
    ('ta', 'Tamil'),
    ('te', 'Telugu'),
]
LANGUAGE_COOKIE_NAME = 'django_language'
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
LANGUAGE_COOKIE_SAMESITE = 'Lax'

TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [BASE_DIR / 'locale']

# ─── Static & Media ───────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / config('MEDIA_ROOT', default='media')

# ─── Email ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@civicai.in')

# ─── Security Settings (production) ───────────────────────────────────────────
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=not DEBUG, cast=bool)
SECURE_PROXY_SSL_HEADER_ENABLED = config(
    'SECURE_PROXY_SSL_HEADER_ENABLED', default=False, cast=bool
)
if not DEBUG and not SECURE_SSL_REDIRECT and not SECURE_PROXY_SSL_HEADER_ENABLED:
    raise ValueError(
        'Production must redirect to HTTPS or explicitly configure a trusted TLS proxy.'
    )
if SECURE_PROXY_SSL_HEADER_ENABLED:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG or config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = not DEBUG or config('CSRF_COOKIE_SECURE', default=False, cast=bool)
SESSION_COOKIE_SAMESITE = config('SESSION_COOKIE_SAMESITE', default='Lax')
CSRF_COOKIE_SAMESITE = config('CSRF_COOKIE_SAMESITE', default='Lax')
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0 if DEBUG else 3600, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=False, cast=bool)
SECURE_REFERRER_POLICY = config('SECURE_REFERRER_POLICY', default='same-origin')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ─── Session ──────────────────────────────────────────────────────────────────
SESSION_COOKIE_AGE = 86400 * 30  # 30 days
SESSION_COOKIE_HTTPONLY = True

# ─── OTP Configuration ────────────────────────────────────────────────────────
OTP_PROVIDER = config('OTP_PROVIDER', default='mock')
if not DEBUG and OTP_PROVIDER == 'mock':
    raise ValueError('OTP_PROVIDER must use a real configured provider when DEBUG is False.')
# Capture the startup decision: Django's test runner temporarily changes
# settings.DEBUG, which must not disable the development provider mid-test.
OTP_MOCK_ALLOWED = DEBUG and OTP_PROVIDER == 'mock'
OTP_EXPIRY_SECONDS = config('OTP_EXPIRY_SECONDS', default=300, cast=int)
OTP_MAX_ATTEMPTS = config('OTP_MAX_ATTEMPTS', default=5, cast=int)
OTP_RESEND_COOLDOWN_SECONDS = config('OTP_RESEND_COOLDOWN_SECONDS', default=60, cast=int)
OTP_IP_REQUEST_LIMIT = config('OTP_IP_REQUEST_LIMIT', default=20, cast=int)
OTP_IP_REQUEST_WINDOW_SECONDS = config('OTP_IP_REQUEST_WINDOW_SECONDS', default=3600, cast=int)

# Provider-specific OTP settings
OTP_PROVIDERS = {
    'mock': {
        'BACKEND': 'apps.accounts.otp.providers.MockOTPProvider',
    },
    'msg91': {
        'BACKEND': 'apps.accounts.otp.providers.MSG91OTPProvider',
        'AUTH_KEY': config('MSG91_AUTH_KEY', default=''),
        'SENDER_ID': config('MSG91_SENDER_ID', default='CIVICAI'),
        'TEMPLATE_ID': config('MSG91_TEMPLATE_ID', default=''),
    },
    'twilio': {
        'BACKEND': 'apps.accounts.otp.providers.TwilioOTPProvider',
        'ACCOUNT_SID': config('TWILIO_ACCOUNT_SID', default=''),
        'AUTH_TOKEN': config('TWILIO_AUTH_TOKEN', default=''),
        'FROM_NUMBER': config('TWILIO_FROM_NUMBER', default=''),
    },
    'fast2sms': {
        'BACKEND': 'apps.accounts.otp.providers.Fast2SMSOTPProvider',
        'API_KEY': config('FAST2SMS_API_KEY', default=''),
    },
    'exotel': {
        'BACKEND': 'apps.accounts.otp.providers.ExotelOTPProvider',
        'ACCOUNT_SID': config('EXOTEL_ACCOUNT_SID', default=''),
        'API_KEY': config('EXOTEL_API_KEY', default=''),
        'API_TOKEN': config('EXOTEL_API_TOKEN', default=''),
        'SUBDOMAIN': config('EXOTEL_SUBDOMAIN', default='api.exotel.com'),
        'SENDER_ID': config('EXOTEL_SENDER_ID', default='CIVICAI'),
    },
}

# ─── AI Configuration ─────────────────────────────────────────────────────────
AI_PROVIDER = config('AI_PROVIDER', default='google')
GOOGLE_API_KEY = config('GOOGLE_API_KEY', default='')
GOOGLE_AI_MODEL = config('GOOGLE_AI_MODEL', default='gemini-1.5-flash')

# ─── REST Framework ───────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '100/hour',
        'anon': '20/hour',
    }
}

# ─── Celery ───────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# ─── Default primary key ──────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
