import os
import json
import sentry_sdk
from .common import *

secrets = json.loads(os.environ.get('SECRETS'))

ENVIRONMENT = os.environ.get('APP_ENV')
DEBUG = ENVIRONMENT == 'development'

BASE_URL = os.environ.get('BASE_URL')

# Security config
SECRET_KEY = secrets['secret_key']
SALT = secrets['salt']
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': secrets['db_name'],
        'USER': secrets['db_user'],
        'PASSWORD': secrets['db_password'],
        'HOST': secrets['db_host'],
        'PORT': secrets['db_port'],
        'ATOMIC_REQUESTS': True,
        'OPTIONS': {
            'connect_timeout': 30
        }
    }
}

# Django Storages S3
AWS_STORAGE_BUCKET_NAME = secrets['aws_storage_bucket_name']
AWS_S3_DIRECT_REGION = secrets['aws_s3_direct_region']
AWS_S3_ENDPOINT_URL = 'https://s3.%s.amazonaws.com' % AWS_S3_DIRECT_REGION
AWS_USE_SSL = 'true'
AWS_S3_ACCESS_KEY_ID = secrets['aws_access_key_id']
AWS_S3_SECRET_ACCESS_KEY = secrets['aws_secret_access_key']

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = secrets['email_host']
EMAIL_HOST_USER = secrets['email_host_user']
EMAIL_HOST_PASSWORD = secrets['email_host_password']
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Celery config
CELERY_TASK_DEFAULT_QUEUE = "/"
CELERY_BROKER_URL = 'amqps://%s:%s@%s/' % (
    secrets['rabbitmq_user'], secrets['rabbitmq_password'], secrets['rabbitmq_host'])
CELERY_RESULT_BACKEND = 'redis://%s/%s' % (
    secrets['redis_host'], secrets['redis_db'])

# Cache ops
CACHEOPS_REDIS = {
    'host': secrets['redis_host'],  # redis-server is on same machine
    'port': 6379,  # default redis port
    'db': 1,  # SELECT non-default redis database
    # using separate redis db or redis instance
    # is highly recommended
    'socket_timeout': 3  # connection timeout in seconds, optional
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://%s/%s' % (secrets['redis_host'], secrets['redis_db']),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'MAX_ENTRIES': 1000
        }
    }
}

# Stripe integration
STRIPE_ENABLED = True
# Changed for development
STRIPE_LIVE_MODE = ENVIRONMENT == 'production'
STRIPE_LIVE_PUBLIC_KEY = secrets['stripe_live_public_key']
STRIPE_LIVE_SECRET_KEY = secrets['stripe_live_secret_key']
# Stripe test configuration
STRIPE_TEST_PUBLIC_KEY = secrets['stripe_test_public_key']
STRIPE_TEST_SECRET_KEY = secrets['stripe_test_secret_key']
DJSTRIPE_WEBHOOK_SECRET = secrets['djstripe_webhook_secret']

# Stripe connect integration
STRIPE_CONNECT_CLIENT_ID = secrets['stripe_connect_client_id']
STRIPE_BASE_AUTH_ERROR_REDIRECT_URL = secrets['stripe_base_auth_error_redirect_url']
DJSTRIPE_CONNECT_WEBHOOK_SECRET = secrets['djstripe_connect_webhook_secret']

# DocuSign integration
DOCUSIGN['BASE_PATH'] = 'docusign.com'
DOCUSIGN['OAUTH_HOST_NAME'] = 'account.docusign.com'
DOCUSIGN['PRIVATE_RSA_KEY'] = """%s""" % secrets['docusign']['private_rsa_key']
DOCUSIGN['INTEGRATION_KEY'] = secrets['docusign']['integration_key']
DOCUSIGN['SECRET_KEY'] = secrets['docusign']['secret_key']

# QuickBooks integration
QUICKBOOKS['CLIENT_ID'] = secrets['quickbooks_client_id']
QUICKBOOKS['CLIENT_SECRET'] = secrets['quickbooks_client_secret']
QUICKBOOKS['BASE_AUTH_ERROR_REDIRECT_URL'] = secrets['quickbooks_base_auth_error_redirect_url']
QUICKBOOKS['ENVIRONMENT'] = 'production'

FIREBASE_CONFIG = secrets['firebase']

# FCM django settings
FCM_DJANGO_SETTINGS['FCM_SERVER_KEY'] = secrets['fcm_server_key']

# Twilio integration
TWILIO_ACCOUNT_SID = secrets['twilio_account_sid']
TWILIO_AUTH_TOKEN = secrets['twilio_auth_token']
TWILIO_SERVICE = secrets['twilio_service']

# Set up debug tools
if DEBUG and not TESTING:
    INSTALLED_APPS += ('django_extensions',)

USE_DEBUG_TOOLBAR = DEBUG

if USE_DEBUG_TOOLBAR and not TESTING:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

if not TESTING:
    sentry_sdk.init(
        environment=ENVIRONMENT,
        **SENTRY_CONFIG
    )

ETH_NETWORK_NAME = secrets['eth_network_name']
ETH_PRIVATE_KEY = secrets['eth_private_key']
ETH_CONTRACT_ADDRESS = secrets['eth_contract_address']
WEB3_INFURA_PROJECT_ID = secrets['web3_infura_project_id']
