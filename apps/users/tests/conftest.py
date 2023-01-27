import pytest

from ...business.factories import LeadFactory
from ...business.models import Lead
from ..factories import (
    AttorneyFactoryWithAllInfo,
    ClientFactory,
    InviteFactory,
)
from ..models import Attorney, Client, Invite


@pytest.fixture(scope='session')
def attorney(django_db_blocker) -> Attorney:
    """Create attorney for users app testing."""
    with django_db_blocker.unblock():
        attorney = AttorneyFactoryWithAllInfo()
        attorney.bar_number = 'qwerty0'
        return attorney


@pytest.fixture(scope='session')
def client(django_db_blocker) -> Client:
    """Create client for users app testing."""
    with django_db_blocker.unblock():
        return ClientFactory()


@pytest.fixture(scope='session')
def other_attorney(django_db_blocker) -> Attorney:
    """Create other attorney for users app testing."""
    with django_db_blocker.unblock():
        return AttorneyFactoryWithAllInfo()


@pytest.fixture(scope='session')
def other_client(django_db_blocker) -> Client:
    """Create other client for users app testing."""
    with django_db_blocker.unblock():
        return ClientFactory()


@pytest.fixture(scope='session', autouse=True)
def invite(
    django_db_blocker, attorney: Attorney, client: Client
) -> Invite:
    """Create invite for testing."""
    with django_db_blocker.unblock():
        return InviteFactory(
            email=client.email,
            user_id=client.user_id,
            inviter_id=attorney.pk
        )


@pytest.fixture(scope='session')
def other_invite(
    django_db_blocker, other_attorney: Attorney, other_client: Client
) -> Invite:
    """Create other invite for testing."""
    with django_db_blocker.unblock():
        return InviteFactory(
            email=other_client.email,
            user_id=other_client.user_id,
            inviter_id=other_attorney.pk
        )


@pytest.fixture(scope='session')
def lead(
    django_db_blocker, attorney: Attorney, client: Client
) -> Lead:
    """Create lead for testing."""
    with django_db_blocker.unblock():
        return LeadFactory(client=client, attorney=attorney, topic=None)
