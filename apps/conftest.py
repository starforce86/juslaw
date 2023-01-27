from typing import Union

from django.db import IntegrityError

from rest_framework.test import APIClient

import pytest

from .business.factories import (
    MatterFactory,
    MatterSharedWithFactory,
    MatterTopicFactory,
)
from .business.models import Lead, Matter, MatterTopic, VideoCall
from .finance.factories import FinanceProfileFactoryWithVerifiedAccount
from .forums.factories import FollowedTopicFactory, TopicFactory
from .forums.models import Topic
from .users.factories import (
    AppUserFactory,
    AttorneyFactory,
    AttorneyVerifiedFactory,
    ClientFactory,
    PaidSupportFactory,
)
from .users.models import AppUser, Attorney, Client, Support


@pytest.fixture(scope='function')
def auth_client_api(client: Client, api_client: APIClient) -> APIClient:
    """Authenticate client and return api client."""
    api_client.force_authenticate(user=client.user)
    return api_client


@pytest.fixture(scope='function')
def auth_attorney_api(attorney: Attorney, api_client: APIClient) -> APIClient:
    """Authenticate attorney and return api client."""
    api_client.force_authenticate(user=attorney.user)
    return api_client


@pytest.fixture(scope='function')
def auth_support_api(support: Support, api_client: APIClient) -> APIClient:
    """Authenticate `support` user and return api client."""
    api_client.force_authenticate(user=support.user)
    return api_client


@pytest.fixture(scope='session')
def client(django_db_blocker, attorney: Attorney) -> Client:
    """Create client for testing."""
    with django_db_blocker.unblock():
        client: Client = ClientFactory()
        client.user.followed_attorneys.add(attorney)
        return client


@pytest.fixture(scope='session')
def attorney(django_db_blocker) -> Attorney:
    """Create attorney for testing."""
    with django_db_blocker.unblock():
        attorney: Attorney = AttorneyVerifiedFactory()
        # Generate finance profile
        FinanceProfileFactoryWithVerifiedAccount(
            user=attorney.user,
        )
        return attorney


@pytest.fixture(scope='session')
def shared_attorney(django_db_blocker, matter: Matter) -> Attorney:
    """Create attorney for testing."""
    with django_db_blocker.unblock():
        attorney = AttorneyFactory()
        try:
            MatterSharedWithFactory(matter=matter, user=attorney.user)
        except IntegrityError:
            pass
        return attorney


@pytest.fixture(scope='session')
def support(django_db_blocker) -> Support:
    """Create support for users app testing."""
    with django_db_blocker.unblock():
        return PaidSupportFactory()


@pytest.fixture(scope='session')
def followed_topic(
    django_db_blocker, attorney: Attorney, client: Client
) -> Topic:
    """Create followed topic by attorney and client for testing."""
    with django_db_blocker.unblock():
        topic: Topic = TopicFactory()
        FollowedTopicFactory(
            follower=attorney.user,
            topic=topic
        )
        FollowedTopicFactory(
            follower=client.user,
            topic=topic
        )
        return topic


@pytest.fixture(scope='session')
def staff(django_db_blocker) -> AppUser:
    """Create staff for testing."""
    with django_db_blocker.unblock():
        return AppUserFactory(is_staff=True)


@pytest.fixture(scope='session')
def other_client(django_db_blocker) -> Client:
    """Create client for testing."""
    with django_db_blocker.unblock():
        return ClientFactory()


@pytest.fixture(scope='session')
def other_attorney(django_db_blocker) -> Attorney:
    """Create attorney for testing."""
    with django_db_blocker.unblock():
        return AttorneyVerifiedFactory()


@pytest.fixture(scope='session')
def other_support(django_db_blocker) -> Support:
    """Create other support for users app testing."""
    with django_db_blocker.unblock():
        return PaidSupportFactory()


@pytest.fixture
def user(
    request,
    client: Client,
    attorney: Attorney,
    support: Support,
    other_client: Client,
    other_attorney: Attorney,
    other_support: Support,
    shared_attorney: Attorney,
) -> Union[AppUser, None]:
    """Fixture to use fixtures in decorator parametrize for AppUser object."""
    mapping = {
        'anonymous': None,
        'client': client,
        'attorney': attorney,
        'support': support,
        'other_client': other_client,
        'other_attorney': other_attorney,
        'other_support': other_support,
        'shared_attorney': shared_attorney,
    }
    param_user = mapping.get(request.param)
    if param_user is None:
        return param_user
    return param_user.user


@pytest.fixture
def other_user(
    request, other_client: Client, other_attorney: Attorney,
    other_support: Support
) -> AppUser:
    """Same as user but to get other user of same type."""
    mapping = {
        'client': other_client,
        'attorney': other_attorney,
        'support': other_support,
    }
    return mapping[request.param].user


@pytest.fixture(scope='session')
def lead(
    django_db_blocker, attorney: Attorney, client: Client
) -> Matter:
    """Create lead for testing."""
    with django_db_blocker.unblock():
        return Lead.objects.create(attorney=attorney, client=client)


@pytest.fixture(scope='session')
def matter(
    django_db_blocker, attorney: Attorney, client: Client, support: Support,
    lead: Lead
) -> Matter:
    """Create matter for testing."""
    with django_db_blocker.unblock():
        matter = MatterFactory(
            attorney=attorney,
            client=client,
            lead=lead,
        )
        try:
            MatterSharedWithFactory(user=support.user, matter=matter)
        except IntegrityError:
            pass
        return matter


@pytest.fixture(scope='session')
def another_matter(django_db_blocker) -> Matter:
    """Create another matter for testing."""
    with django_db_blocker.unblock():
        return MatterFactory()


@pytest.fixture(scope='session')
def matter_topic(django_db_blocker, matter: Matter) -> MatterTopic:
    """Create matter topic for testing."""
    with django_db_blocker.unblock():
        return MatterTopicFactory(matter=matter)


@pytest.fixture(scope='session')
def other_matter_topic(django_db_blocker) -> MatterTopic:
    """Create topic for testing."""
    with django_db_blocker.unblock():
        return MatterTopicFactory()


@pytest.fixture(scope='session')
def attorney_video_call(
    django_db_blocker,
    attorney: Attorney,
    client: Client,
) -> VideoCall:
    """Create video call that was created for client and attorney."""
    with django_db_blocker.unblock():
        video_call = VideoCall.objects.create()
        video_call.participants.add(attorney.pk, client.pk)
        return video_call


@pytest.fixture(scope='session')
def shared_attorney_video_call(
    django_db_blocker,
    shared_attorney: Attorney,
    client: Client,
) -> VideoCall:
    """Create video call that was created for client and shared attorney."""
    with django_db_blocker.unblock():
        video_call = VideoCall.objects.create()
        video_call.participants.add(shared_attorney.pk, client.pk)
        return video_call


@pytest.fixture(scope='session')
def support_video_call(
    django_db_blocker,
    support: Support,
    client: Client,
) -> VideoCall:
    """Create video call that was created for client and support."""
    with django_db_blocker.unblock():
        video_call = VideoCall.objects.create()
        video_call.participants.add(support.pk, client.pk)
        return video_call


@pytest.fixture
def stripe_create_payment_intent(mocker):
    """Mock stripe.PaymentIntent.create."""
    return mocker.patch(
        'stripe.PaymentIntent.create',
        return_value={
            "id": "pi_",
            "object": "payment_intent",
            "amount": 1000,
            "amount_capturable": 0,
            "amount_received": 0,
            "application": None,
            "application_fee_amount": None,
            "canceled_at": None,
            "cancellation_reason": None,
            "capture_method": "automatic",
            "client_secret": "pi_",
            "confirmation_method": "automatic",
            "created": 1577092736,
            "currency": "usd",
            "customer": None,
            "description": "Created by stripe.com/docs demo",
            "invoice": None,
            "last_payment_error": None,
            "livemode": False,
            "metadata": {},
            "next_action": None,
            "on_behalf_of": None,
            "payment_method": None,
            "payment_method_options": {
                "card": {
                    "installments": None,
                    "network": None,
                    "request_three_d_secure": "automatic"
                }
            },
            "payment_method_types": [
                "card"
            ],
            "receipt_email": None,
            "review": None,
            "setup_future_usage": None,
            "shipping": None,
            "statement_descriptor": None,
            "statement_descriptor_suffix": None,
            "status": "requires_payment_method",
            "transfer_data": None,
            "transfer_group": None
        }
    )
