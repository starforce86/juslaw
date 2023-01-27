import pytest
from djstripe.enums import SubscriptionStatus

from apps.users.factories import (
    AppUserWithAttorneyFactory,
    AttorneyVerifiedFactory,
)
from apps.users.models import Attorney

from .. import factories, models


@pytest.fixture(scope='session')
def attorney(django_db_blocker) -> Attorney:
    """Create attorney for testing."""
    with django_db_blocker.unblock():
        attorney: Attorney = AttorneyVerifiedFactory()
        return attorney


@pytest.fixture(scope="module")
def product(django_db_blocker) -> models.ProductProxy:
    """Create ProductProxy object."""
    with django_db_blocker.unblock():
        return factories.ProductProxyFactory()


@pytest.fixture(scope="module")
def plan(django_db_blocker) -> models.PlanProxy:
    """Create PlanProxy object."""
    with django_db_blocker.unblock():
        return factories.PlanProxyFactory()


@pytest.fixture(scope="module")
def another_plan(django_db_blocker) -> models.PlanProxy:
    """Create another PlanProxy object."""
    with django_db_blocker.unblock():
        return factories.PlanProxyFactory()


@pytest.fixture(scope="module")
def customer(django_db_blocker) -> models.CustomerProxy:
    """Create CustomerProxy object."""
    with django_db_blocker.unblock():
        return factories.CustomerProxyFactory(
            subscriber=AppUserWithAttorneyFactory()
        )


@pytest.fixture(scope="module")
def subscription(
    django_db_blocker, customer
) -> models.SubscriptionProxy:
    """Create SubscriptionProxy object."""
    with django_db_blocker.unblock():
        subscription = factories.SubscriptionProxyFactory(
            customer=customer,
            status=SubscriptionStatus.trialing
        )
        customer.subscriber.active_subscription = subscription
        customer.subscriber.save()
        return subscription


@pytest.fixture(scope="module")
def another_subscription(django_db_blocker) -> models.SubscriptionProxy:
    """Create another SubscriptionProxy object."""
    with django_db_blocker.unblock():
        return factories.SubscriptionProxyFactory()


@pytest.fixture(scope="module")
def finance_profile(django_db_blocker, customer) -> models.FinanceProfile:
    """Create FinanceProfile object."""
    with django_db_blocker.unblock():
        return factories.FinanceProfileFactory(user=customer.subscriber)
