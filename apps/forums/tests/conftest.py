import pytest

from apps.forums.factories import CategoryFactory, PostFactory, TopicFactory
from apps.forums.models import Topic
from apps.users.factories import ClientFactory
from apps.users.models import Attorney, Client


@pytest.fixture(scope='session')
def client_topic(django_db_blocker, client: Client) -> Topic:
    """Create clients topic for testing."""
    with django_db_blocker.unblock():
        topic = TopicFactory()
        topic.first_post = PostFactory(
            topic=topic,
            author=client.user,
        )
        topic.save()
        return topic


@pytest.fixture(scope='session')
def client_with_same_state(django_db_blocker, attorney: Attorney) -> Client:
    """Create client with same state as attorney's."""
    with django_db_blocker.unblock():
        client = ClientFactory(state=attorney.practice_jurisdictions.first())
        return client


@pytest.fixture(scope='session')
def opportunity_with_keywords(
    django_db_blocker,
    client_with_same_state: Client,
    attorney: Attorney
) -> Topic:
    """Create opportunity with keywords match."""
    with django_db_blocker.unblock():
        topic = TopicFactory()
        topic.first_post = PostFactory(
            topic=topic,
            author=client_with_same_state.user,
            text=' '.join(attorney.keywords)
        )
        topic.save()
        return topic


@pytest.fixture(scope='session')
def opportunity_with_speciality(
    django_db_blocker,
    client_with_same_state: Client,
    attorney: Attorney
) -> Topic:
    """Create opportunity with speciality match."""
    with django_db_blocker.unblock():
        topic = TopicFactory(
            category=CategoryFactory(
                speciality=attorney.user.specialities.first()
            )
        )
        topic.first_post = PostFactory(
            topic=topic,
            author=client_with_same_state.user,
        )
        topic.save()
        return topic


@pytest.fixture(scope='session')
def not_opportunity(
    django_db_blocker, attorney: Attorney
) -> Topic:
    """Create topic that are not opportunity."""
    with django_db_blocker.unblock():
        topic = TopicFactory(
            category=CategoryFactory(
                speciality=attorney.user.specialities.first()
            )
        )
        topic.first_post = PostFactory(
            topic=topic,
            author=ClientFactory(state=None).user,
            text=' '.join(attorney.keywords)
        )
        topic.save()
        return topic
