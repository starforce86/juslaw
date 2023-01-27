import os
import json

from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from libs.utils import get_latest_version

secrets = json.loads(os.environ.get('SECRETS'))

def before_send(event, hint):
    """Remove sensitive data about user."""
    from django.conf import settings
    if 'user' in event and settings.ENVIRONMENT == 'production':
        event['user'] = {
            'id': event['user'].get('id')
        }
    return event


# https://docs.sentry.io/error-reporting/configuration/?platform=python
SENTRY_CONFIG = {
    # The DSN tells the SDK where to send the events to.
    'dsn': secrets['sentry_dsn'],
    # Adds django and celery support
    'integrations': [
        DjangoIntegration(),
        CeleryIntegration(),
        RedisIntegration(),
    ],
    'attach_stacktrace': True,
    'send_default_pii': True,
    # Adds a body of request
    'request_bodies': 'always',
    'before_send': before_send,
    'release': get_latest_version(
        'changelog_backend/changelog.md'
    )
}
