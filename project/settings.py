"""
Generated by 'django-admin startproject' using Django 3.1.3.
"""

from pathlib import Path
import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

env = os.environ

PROJECT_SLUG = "commonology"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/
SECRET_KEY = env.get("DJANGO_SECRET_KEY", '!6^d23vriql_*qgxfp7^zg+3j2(0di&!lpf+_6d1eb(is7()m7')

DEBUG = env.get("DEBUG", False)

ALLOWED_HOSTS = ['127.0.0.1', 'commonologygame.com', 'staging.commonologygame.com', 'staging.quizitive.com']
INTERNAL_IPS = ('127.0.0.1', 'staging.commonologygame.com', )

# Disable Django Debug Toolbar
# NOTE: Much slower on database intensive operations
# NOTE: Disabling this will enable Google Analytics. Comment out the script in base.html.
if os.environ.get('DISABLE_DEBUG_TOOLBAR'):
    INTERNAL_IPS = ()

DEBUG_TOOLBAR_CONFIG = {'PRETTIFY_SQL': False}

# Enable Django Debug Toolbar
# NOTE: Much slower on database intensive operations
if os.environ.get('DEBUG_TOOLBAR'):
    INTERNAL_IPS = ['127.0.0.1', 'staging.commonologygame.com']
    DEBUG_TOOLBAR_CONFIG = {'PRETTIFY_SQL': False}

# Celery Configuration Options
CELERY_TIMEZONE = 'America/New_York'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/New_York'

# if env.get('EAGER_CELERY', False):
#     CELERY_TASK_ALWAYS_EAGER = True
#     CELERY_TASK_EAGER_PROPAGATES = True
#     BROKER_BACKEND = 'memory'

# Application definition
INSTALLED_APPS = [
    'sslserver',
    'users',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mail',
    'community',
    'game',
    'leaderboard',
    'debug_toolbar'
]

AUTH_USER_MODEL = 'users.Player'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]

ROOT_URLCONF = 'project.urls'

# These redirects are needed for the users app.
LOGIN_REDIRECT_URL = "leaderboard"
LOGOUT_REDIRECT_URL = "home"

SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'prefix': 'session',
    'socket_timeout': 1
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": PROJECT_SLUG
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': PROJECT_SLUG,
        'HOST': '127.0.0.1',
        'PORT': 5432,
        'USER': 'postgres',
        'PASSWORD': 'postgres',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
TIME_ZONE = 'UTC'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'project/static')
]

if env.get("INHIBIT_MAIL", False) == 'True':
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_APIKEY')
DEFAULT_FROM_EMAIL = 'concierge@commonologygame.com'

MAILCHIMP_API_KEY = os.getenv('MAILCHIMP_APIKEY')
MAILCHIMP_HOOK_UUID = os.getenv('MAILCHIMP_HOOK_UUID')
MAILCHIMP_SERVER = 'us2'
MAILCHIMP_PRODUCTION_LIST_ID = '4f9a2e9bd6'
MAILCHIMP_STAGING_LIST_ID = '36b9567454'
MAILCHIMP_EMAIL_LIST_ID = os.getenv('MAILCHIMP_AUDIENCE')


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Sentry
SENTRY_KEY = os.environ.get('SENTRY_KEY')
sentry_sdk.init(
    dsn=f"https://{SENTRY_KEY}@o520957.ingest.sentry.io/5631994",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.2,
    send_default_pii=True
)
