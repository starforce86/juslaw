import io

from django.conf import settings

from rest_framework.test import APIClient

import pytest
from PIL import Image

from libs.django_cities_light.factories import CountryFactory

from apps.news.models import News
from apps.social.models import AttorneyPost


def pytest_sessionstart():
    """Set up settings for tests.

    Make django sent emails to console.
    Set storage to `FileSystemStorage`.
    Make celery tasks run without workers.
    Disable stripe.
    Disable firebase.
    Disable fcm notifications.
    Reset docusign settings.

    We set up settings, since important settings that we would set up in
    common/testing.py would be overridden by environment settings.

    """
    # The default password hasher is rather slow by design.
    # https://docs.djangoproject.com/en/3.0/topics/testing/overview/
    settings.PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )
    settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    settings.DEFAULT_FILE_STORAGE = (
        'django.core.files.storage.FileSystemStorage'
    )

    # To disable celery in tests
    settings.CELERY_TASK_ALWAYS_EAGER = True

    settings.STRIPE_ENABLED = False
    settings.FIREBASE_ENABLED = False
    settings.FCM_FIREBASE_ENABLED = False
    settings.DOCUSIGN.update({
        'TOKEN_EXPIRATION': 3600,
        'PRIVATE_RSA_KEY': None,
        'BASE_PATH': None,
        'OAUTH_HOST_NAME': None,
        'INTEGRATION_KEY': None,
        'SECRET_KEY': None,
    })
    # To disable stripe in tests
    settings.STRIPE_TEST_PUBLIC_KEY = 'pk_test_'
    settings.STRIPE_TEST_SECRET_KEY = 'sk_test_'
    settings.DJSTRIPE_WEBHOOK_SECRET = 'whsec_'
    settings.DJSTRIPE_CONNECT_WEBHOOK_SECRET = 'whsec_'


@pytest.fixture(scope='session', autouse=True)
def set_up_tmp_media(tmpdir_factory):
    """Set up for media folder for testing.

    tmpdir_factory can create temporary folder for testing, which will be clean
    up by pytest. Use are using it to set up media folder for testing, instead
    of using the original one(be cause after many pytest runs, there will be
    lots of useless files, that we would need to clean up, but now pytest
    does this for us)

    """
    tmp_media = tmpdir_factory.mktemp('tmp_media')
    settings.MEDIA_ROOT = str(tmp_media)


@pytest.fixture(scope='session', autouse=True)
def django_db_setup(request, django_db_setup, django_db_blocker):
    """Set up test db for testing."""
    def tear_down_django_db_setup():
        """Remove models which are using ImageSpecField.

        Because our media folder is temporary, next we will run tests,
        ImageSpecField will fail to generate thumbnails for instance from
        previous runs, because there no more file to generate thumbnail from.

        """
        with django_db_blocker.unblock():
            AttorneyPost.objects.all().delete()
            News.objects.all().delete()
    request.addfinalizer(tear_down_django_db_setup)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Give all tests access to db."""


@pytest.fixture(scope='session', autouse=True)
def generate_locations(django_db_blocker):
    """Generate locations for testing session."""
    with django_db_blocker.unblock():
        CountryFactory()


@pytest.fixture
def status_code(request) -> int:
    """Fixture to parametrize status codes."""
    return request.param


@pytest.fixture
def attr_to_check(request) -> int:
    """Fixture to parametrize attr param."""
    return request.param


@pytest.fixture
def model(request):
    """Fixture to parametrize model param."""
    return request.param


@pytest.fixture
def model_factory(request):
    """Fixture to parametrize model_factory param."""
    return request.param


@pytest.fixture(scope='function')
def api_client() -> APIClient:
    """Create api client."""
    return APIClient()


@pytest.fixture(scope='session')
def image_file():
    """Generate image file for testing."""
    width = 100
    height = width
    color = 'blue'
    image_format = 'JPEG'

    thumb = Image.new('RGB', (width, height), color)
    thumb_io = io.BytesIO()
    thumb.save(thumb_io, format=image_format)
    return thumb_io.getvalue()
