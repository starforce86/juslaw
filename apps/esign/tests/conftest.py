import pytest

from apps.business.models import Matter

from .. import factories, models


@pytest.fixture(scope="function")
def envelope(django_db_blocker, matter: Matter) -> models.Envelope:
    """Create Envelope object."""
    with django_db_blocker.unblock():
        return factories.EnvelopeFactory(matter=matter)


@pytest.fixture(scope="function")
def another_envelope(
    django_db_blocker, another_matter: Matter
) -> models.Envelope:
    """Create another Envelope object."""
    with django_db_blocker.unblock():
        return factories.EnvelopeFactory(matter=another_matter)


@pytest.fixture(scope="function")
def esign_profile(django_db_blocker) -> models.ESignProfile:
    """Create ESignProfile object."""
    with django_db_blocker.unblock():
        return factories.ESignProfileFactory()


@pytest.fixture(scope="function")
def another_esign_profile(django_db_blocker) -> models.ESignProfile:
    """Create another ESignProfile object."""
    with django_db_blocker.unblock():
        return factories.ESignProfileFactory()
