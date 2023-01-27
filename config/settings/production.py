from .common import *

DEBUG = False
ENVIRONMENT = 'production'

BASE_URL = 'https://backend.jus-law.com'

# Security config
SECRET_KEY = '{{$.SECRET_KEY}}'
SALT = '{{$.SALT}}'
ALLOWED_HOSTS = ['*']

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
AWS_STORAGE_BUCKET_NAME = '{{$.AWS_STORAGE_BUCKET_NAME}}'
AWS_S3_DIRECT_REGION = '{{$.AWS_S3_DIRECT_REGION}}'
AWS_S3_ENDPOINT_URL = 'https://s3.%s.amazonaws.com' % AWS_S3_DIRECT_REGION
AWS_USE_SSL = 'true'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = '{{$.EMAIL_HOST}}'
EMAIL_HOST_USER = '{{$.EMAIL_HOST_USER}}'
EMAIL_HOST_PASSWORD = '{{$.EMAIL_HOST_PASSWORD}}'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Celery config
CELERY_TASK_DEFAULT_QUEUE = '{{$.CELERY_QUEUE}}'
CELERY_BROKER_URL = 'amqp://{{$.RABBITMQ_USER}}:{{$.RABBITMQ_PASSWORD}}@{{$.RABBITMQ_HOST}}/{{$.CELERY_QUEUE}}'
CELERY_RESULT_BACKEND = 'redis://{{$.REDIS_HOST}}/{{$.REDIS_DB}}'

# Cache ops
CACHEOPS_REDIS = {
    'host': '{{$.REDIS_HOST}}',  # redis-server is on same machine
    'port': 6379,  # default redis port
    'db': 1,  # SELECT non-default redis database
    # using separate redis db or redis instance
    # is highly recommended
    'socket_timeout': 3  # connection timeout in seconds, optional
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
STRIPE_ENABLED = True
STRIPE_LIVE_MODE = True
STRIPE_LIVE_PUBLIC_KEY = '{{$.STRIPE_LIVE_PUBLIC_KEY}}'
STRIPE_LIVE_SECRET_KEY = '{{$.STRIPE_LIVE_SECRET_KEY}}'
DJSTRIPE_WEBHOOK_SECRET = '{{$.DJSTRIPE_WEBHOOK_SECRET}}'

# Stripe connect integration
STRIPE_CONNECT_CLIENT_ID = '{{$.STRIPE_CONNECT_CLIENT_ID}}'
STRIPE_BASE_AUTH_ERROR_REDIRECT_URL = '{{$.STRIPE_BASE_AUTH_ERROR_REDIRECT_URL}}'
DJSTRIPE_CONNECT_WEBHOOK_SECRET = '{{$.DJSTRIPE_CONNECT_WEBHOOK_SECRET}}'

# DocuSign integration
DOCUSIGN['BASE_PATH'] = 'docusign.com'
DOCUSIGN['OAUTH_HOST_NAME'] = 'account.docusign.com'
DOCUSIGN['PRIVATE_RSA_KEY'] = """{{$.DOCUSIGN.PRIVATE_RSA_KEY}}"""
DOCUSIGN['INTEGRATION_KEY'] = '{{$.DOCUSIGN.INTEGRATION_KEY}}'
DOCUSIGN['SECRET_KEY'] = '{{$.DOCUSIGN.SECRET_KEY}}'

# QuickBooks integration
QUICKBOOKS['CLIENT_ID'] = '{{$.QUICKBOOKS_CLIENT_ID}}'
QUICKBOOKS['CLIENT_SECRET'] = '{{$.QUICKBOOKS_CLIENT_SECRET}}'
QUICKBOOKS['BASE_AUTH_ERROR_REDIRECT_URL'] = '{{$.QUICKBOOKS_BASE_AUTH_ERROR_REDIRECT_URL}}'
QUICKBOOKS['ENVIRONMENT'] = 'production'

# FCM django settings
FCM_DJANGO_SETTINGS['FCM_SERVER_KEY'] = '{{$.FCM_SERVER_KEY}}'

# Twilio integration
TWILIO_ACCOUNT_SID = '{{$.TWILIO_ACCOUNT_SID}}'
TWILIO_AUTH_TOKEN = '{{$.TWILIO_AUTH_TOKEN}}'
TWILIO_SERVICE = '{{$.TWILIO_SERVICE}}'
