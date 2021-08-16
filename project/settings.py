"""
Generated by 'django-admin startproject' using Django 3.1.3.
"""

from pathlib import Path
import os
from os import environ as env
import sys
import platform
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


IS_TEST = 'test' in sys.argv

project_name = env.get("PROJECT_NAME", 'commonology')
DOMAIN = 'commonologygame.com'

DEBUG = env.get("DEBUG", False)
DEBUG_TOOLBAR = env.get("DEBUG_TOOLBAR", False)
DEBUG_TOOLBAR_CONFIG = {'PRETTIFY_SQL': False}
EXTRA_ALLOWED_HOST = env.get('EXTRA_ALLOWED_HOST')

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = env.get("DJANGO_SECRET_KEY", '!6^d23vriql_*qgxfp7^zg+3j2(0di&!lpf+_6d1eb(is7()m7')

DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 100

ALLOWED_HOSTS = ['127.0.0.1', DOMAIN, 'staging.' + DOMAIN]
if EXTRA_ALLOWED_HOST:
    ALLOWED_HOSTS.append(EXTRA_ALLOWED_HOST)

INTERNAL_IPS = ()
if DEBUG:
    INTERNAL_IPS = ('127.0.0.1', 'staging.' + DOMAIN)

USE_TZ = True
TIME_ZONE = 'America/New_York'

CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

if env.get('EAGER_CELERY', False):
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    BROKER_BACKEND = 'memory'

INSTALLED_APPS = [
    'channels',
    'sslserver',
    'users',
    'ckeditor',
    'ckeditor_uploader',
    'django_object_actions',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',
    'chat',
    'game',
    'leaderboard',
    'mail',
    'quizitive',
]

if DEBUG_TOOLBAR:
    INSTALLED_APPS.append('debug_toolbar')

AUTH_USER_MODEL = 'users.Player'

# configuration for social authentication
SOCIAL_AUTH_JSONFIELD_ENABLED = True
AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'users.utils.add_additional_fields'
)

RECAPTCHA3_KEY = env.get('RECAPTCHA3_KEY')
RECAPTCHA3_SECRET = env.get('RECAPTCHA3_SECRET')


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG_TOOLBAR:
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

ROOT_URLCONF = 'project.urls'

# These redirects are needed for the users app.
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
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
        "KEY_PREFIX": project_name
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'project/templates')],
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

# Django channels settings
ASGI_APPLICATION = 'project.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': project_name,
        'HOST': '127.0.0.1',
        'PORT': 5432,
        'USER': 'postgres',
        'PASSWORD': 'postgres',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

STATIC_URL = '/static/'
STATIC_ROOT = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'project/static')
]

CKEDITOR_JQUERY_URL = 'https://ajax.googleapis.com/ajax/libs/jquery/2.2.4/jquery.min.js'
CKEDITOR_UPLOAD_PATH = "ckeditor_uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"
MEDIA_URL = '/media/'
MEDIA_ROOT = 'media/'

if env.get("ENABLE_MAIL"):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = env.get('SENDGRID_APIKEY', 'foo')
DEFAULT_FROM_EMAIL = 'concierge@' + DOMAIN
DEFAULT_FROM_EMAIL_NAME = 'Commonology'

ALEX_FROM_EMAIL = 'alex@commonologygame.com'
ALEX_FROM_NAME = 'Alex Fruin'

MAILCHIMP_API_KEY = env.get('MAILCHIMP_APIKEY')
MAILCHIMP_HOOK_UUID = env.get('MAILCHIMP_HOOK_UUID')
MAILCHIMP_SERVER = 'us2'
MAILCHIMP_EMAIL_LIST_ID = env.get("MAILCHIMP_EMAIL_LIST_ID")

GOOGLE_GSPREAD_API_CONFIG = os.path.join(BASE_DIR, '.config/gspread/commonology_service_account.json')
GOOGLE_DRIVE_FOLDER_ID = env.get("GOOGLE_DRIVE_FOLDER_ID")

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
        'level': 'INFO',
    },
}

if 'SENTRY_KEY' in env:
    SENTRY_KEY = env.get('SENTRY_KEY')
    sentry_sdk.init(dsn=f"https://{SENTRY_KEY}@o520957.ingest.sentry.io/5726202",
                    integrations=[DjangoIntegration()],
                    traces_sample_rate=0.2,
                    send_default_pii=True)


CKEDITOR_CONFIGS = {
    'default': {
        'toolbar_Basic': [
            ['Source', '-', 'Bold', 'Italic']
        ],
        'toolbar_complete': [
            {'name': 'document', 'items': ['Source', '-', 'Save', 'NewPage', 'Preview', 'Print', '-', 'Templates']},
            {'name': 'clipboard', 'items': ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo']},
            {'name': 'editing', 'items': ['Find', 'Replace', '-', 'SelectAll']},
            {'name': 'forms',
             'items': ['Form', 'Checkbox', 'Radio', 'TextField', 'Textarea', 'Select', 'Button', 'ImageButton',
                       'HiddenField']},
            '/',
            {'name': 'basicstyles',
             'items': ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat']},
            {'name': 'paragraph',
             'items': ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', 'CreateDiv', '-',
                       'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock', '-', 'BidiLtr', 'BidiRtl',
                       'Language']},
            {'name': 'links', 'items': ['Link', 'Unlink', 'Anchor']},
            {'name': 'insert',
             'items': ['Image', 'Flash', 'Table', 'HorizontalRule', 'Smiley', 'SpecialChar', 'PageBreak', 'Iframe']},
            '/',
            {'name': 'styles', 'items': ['Styles', 'Format', 'Font', 'FontSize']},
            {'name': 'colors', 'items': ['TextColor', 'BGColor']},
            {'name': 'tools', 'items': ['Maximize', 'ShowBlocks']},
            {'name': 'about', 'items': ['About']},
            '/',  # put this to force next toolbar on new line
            {'name': 'yourcustomtools', 'items': [
                # put the name of your editor.ui.addButton here
                'Preview',
                'Maximize',

            ]},
        ],
        'toolbar': 'complete',  # put selected toolbar config here
        'tabSpaces': 4,
        'disallowedContent': 'script',
        'font_names': 'Poppins;Verdana;Roboto;sans-serif',
        'extraPlugins': ','.join([
            'uploadimage',
            'div',
            'autolink',
            'autoembed',
            'embedsemantic',
            'autogrow',
            'widget',
            'lineutils',
            'clipboard',
            'dialog',
            'dialogui',
            'elementspath'
        ]),
    }
}
