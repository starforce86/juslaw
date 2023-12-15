from .common import *

import sentry_sdk

DEBUG = True
ENVIRONMENT = 'development'

BASE_URL = '{{$.BASE_URL}}'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': '{{$.DB_NAME}}',
        'USER': '{{$.DB_USER}}',
        'PASSWORD': '{{$.DB_PASSWORD}}',
        'HOST': '{{$.DB_HOST}}',
        'PORT': '{{$.DB_PORT}}',
        'ATOMIC_REQUESTS': True,
        'OPTIONS': {
            'connect_timeout': 30,
        },
    }
}

# Django Storages S3
AWS_IS_MINIO = {{$.AWS_IS_MINIO}}
AWS_S3_ACCESS_KEY_ID = '{{$.AWS_S3_ACCESS_KEY_ID}}'
AWS_S3_SECRET_ACCESS_KEY = '{{$.AWS_S3_SECRET_ACCESS_KEY}}'
AWS_S3_ENDPOINT_URL = '{{$.AWS_S3_ENDPOINT_URL}}'
AWS_STORAGE_BUCKET_NAME = '{{$.AWS_STORAGE_BUCKET_NAME}}'
AWS_S3_DIRECT_REGION = '{{$.AWS_S3_DIRECT_REGION}}'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = '{{$.EMAIL_HOST}}'
EMAIL_HOST_USER = '{{$.EMAIL_HOST_USER}}'
EMAIL_HOST_PASSWORD = '{{$.EMAIL_HOST_PASSWORD}}'
EMAIL_PORT = {{$.EMAIL_PORT}}
EMAIL_USE_TLS = {{$.EMAIL_USE_TLS}}

# Celery config
CELERY_TASK_DEFAULT_QUEUE = '{{$.CELERY_QUEUE}}'
CELERY_BROKER_URL = 'amqp://{{$.RABBITMQ_USER}}:{{$.RABBITMQ_PASSWORD}}@{{$.RABBITMQ_HOST}}/{{$.CELERY_QUEUE}}'
CELERY_RESULT_BACKEND = 'redis://{{$.REDIS_HOST}}/{{$.REDIS_DB}}'

# Cache ops
CACHEOPS_REDIS = {
    'host': '{{$.REDIS_HOST}}',
    'port': 6379,
    'db': {{$.REDIS_DB}},
    'socket_timeout': 3
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://{{$.REDIS_HOST}}/{{$.REDIS_DB}}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'MAX_ENTRIES': 1000,
        },
    }
}

# Stripe integration
STRIPE_TEST_PUBLIC_KEY = '{{$.STRIPE_TEST_PUBLIC_KEY}}'
STRIPE_TEST_SECRET_KEY = '{{$.STRIPE_TEST_SECRET_KEY}}'
DJSTRIPE_WEBHOOK_SECRET = '{{$.DJSTRIPE_WEBHOOK_SECRET}}'

# Stripe connect integration
STRIPE_CONNECT_CLIENT_ID = '{{$.STRIPE_CONNECT_CLIENT_ID}}'
STRIPE_BASE_AUTH_ERROR_REDIRECT_URL = '{{$.STRIPE_BASE_AUTH_ERROR_REDIRECT_URL}}'
DJSTRIPE_CONNECT_WEBHOOK_SECRET = '{{$.DJSTRIPE_CONNECT_WEBHOOK_SECRET}}'

# Vault setting
VAULT_STORAGE = 'jlp-backend-develop'

# DocuSign integration
DOCUSIGN['PRIVATE_RSA_KEY'] = """{{$.DOCUSIGN.PRIVATE_RSA_KEY}}"""
DOCUSIGN['OAUTH_HOST_NAME'] = '{{$.DOCUSIGN.OAUTH_HOST_NAME}}'
DOCUSIGN['INTEGRATION_KEY'] = '{{$.DOCUSIGN.INTEGRATION_KEY}}'
DOCUSIGN['SECRET_KEY'] = '{{$.DOCUSIGN.SECRET_KEY}}'

# QuickBooks integration
QUICKBOOKS['CLIENT_ID'] = '{{$.QUICKBOOKS_CLIENT_ID}}'
QUICKBOOKS['CLIENT_SECRET'] = '{{$.QUICKBOOKS_CLIENT_SECRET}}'
QUICKBOOKS['BASE_AUTH_ERROR_REDIRECT_URL'] = '{{$.QUICKBOOKS_BASE_AUTH_ERROR_REDIRECT_URL}}'

DEFAULT_PLAN_ID = '{{$.DEFAULT_PLAN_ID}}'

# FCM django settings
FCM_DJANGO_SETTINGS['FCM_SERVER_KEY'] = '{{$.FCM_SERVER_KEY}}'

# Twilio integration
TWILIO_ACCOUNT_SID = '{{$.TWILIO_ACCOUNT_SID}}'
TWILIO_AUTH_TOKEN = '{{$.TWILIO_AUTH_TOKEN}}'
TWILIO_SERVICE = '{{$.TWILIO_SERVICE}}'

# Set up debug tools
if DEBUG and not TESTING:
    INSTALLED_APPS += ('django_extensions',)

USE_DEBUG_TOOLBAR = {{$.USE_DEBUG_TOOLBAR}}
if USE_DEBUG_TOOLBAR and not TESTING:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

if not TESTING:
    sentry_sdk.init(
        environment=ENVIRONMENT,
        **SENTRY_CONFIG
    )

# DRF_API_LOGGER_DATABASE = True
# DRF_API_LOGGER_SIGNAL = True
# DRF_LOGGER_QUEUE_MAX_SIZE = 10
# DRF_LOGGER_INTERVAL = 10
# DRF_API_LOGGER_SLOW_API_ABOVE = 200
