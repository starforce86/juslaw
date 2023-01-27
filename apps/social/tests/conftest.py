from typing import Union

import pytest

from apps.users.factories import AttorneyFactory

from ...users.models import AppUser, Attorney, Client
from .. import factories, models


@pytest.fixture(scope='session')
def attorney_group_chat(
    django_db_blocker, attorney: Attorney
) -> models.GroupChat:
    """Create GroupChat for attorney."""
    with django_db_blocker.unblock():
        network = factories.GroupChatFactory(creator_id=attorney.pk)
        network.participants.set([attorney.pk])
        return network


@pytest.fixture(scope='session')
def participant(
    django_db_blocker, attorney_group_chat: models.GroupChat
) -> models.GroupChat:
    """Create attorney for chat participants."""
    with django_db_blocker.unblock():
        participant = AttorneyFactory()
        attorney_group_chat.participants.add(participant.pk)
        return participant


@pytest.fixture(scope='session')
def other_attorney_group_chat(
    django_db_blocker, attorney: Attorney, other_attorney: Attorney
) -> models.GroupChat:
    """Create GroupChat for other attorney."""
    with django_db_blocker.unblock():
        return factories.GroupChatFactory(creator_id=other_attorney.pk)


@pytest.fixture
def group_chat(
    request,
    attorney_group_chat: models.GroupChat,
    other_attorney_group_chat: models.GroupChat
) -> models.GroupChat:
    """Fixture to use fixtures in decorator parametrize for GroupChat."""
    mapping = {
        'attorney_group_chat': attorney_group_chat,
        'other_attorney_group_chat': other_attorney_group_chat,
    }
    return mapping.get(request.param)


@pytest.fixture(scope='session')
def attorney_post(
    django_db_blocker, attorney: Attorney
) -> models.AttorneyPost:
    """Create AttorneyPost for attorney."""
    with django_db_blocker.unblock():
        return factories.AttorneyPostFactory(author=attorney)


@pytest.fixture(scope='session')
def other_attorney_post(
    django_db_blocker, other_attorney: Attorney
) -> models.AttorneyPost:
    """Create AttorneyPost for other attorney."""
    with django_db_blocker.unblock():
        return factories.AttorneyPostFactory(author=other_attorney)


@pytest.fixture
def user(
    request,
    client: Client,
    attorney: Attorney,
    other_attorney: Attorney,
    participant: Attorney
) -> Union[AppUser, None]:
    """Fixture to use fixtures in decorator parametrize for AppUser object."""
    mapping = {
        'anonymous': None,
        'client': client,
        'attorney': attorney,
        'other_attorney': other_attorney,
        'participant': participant,
    }
    param_user = mapping.get(request.param)
    if param_user is None:
        return param_user
    return param_user.user
