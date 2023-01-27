from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import NOT_FOUND, OK

from ....users.models import AppUser
from ... import models
from ...factories import ActivityFactory


def get_list_url():
    """Get url for activity list retrieval."""
    return reverse_lazy('v1:activities-list')


def get_detail_url(activity: models.Activity):
    """Get url for activity retrieval."""
    return reverse_lazy(
        'v1:activities-detail', kwargs={'pk': activity.pk}
    )


@pytest.fixture(scope='module')
def activity(django_db_blocker, matter: models.Matter) -> models.Activity:
    """Create activity for testing."""
    with django_db_blocker.unblock():
        return ActivityFactory(matter=matter)


@pytest.fixture(scope='module')
def other_activity(django_db_blocker) -> models.Activity:
    """Create other activities for testing."""
    with django_db_blocker.unblock():
        return ActivityFactory()


class TestAuthUserAPI:
    """Test activities api for auth users.

    Client can read activities from its related matters.
    Attorneys can read activities from their own matters or shared with them
    matters.
    Support can read activities from shared with them matters.

    """

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney',
            # check that shared activity can be get too
            'shared_attorney',
            'support',
        ),
        indirect=True
    )
    def test_get_list_activity(
        self, api_client: APIClient, user: AppUser, activity: models.Activity,
        other_activity: models.Activity
    ):
        """Test that users can get list of activities."""
        activity.matter.status = models.Matter.STATUS_OPEN
        activity.matter.save()

        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == OK

        activities_expected = set(
            models.Activity.objects.available_for_user(
                user=user
            ).values_list('pk', flat=True)
        )
        activities_result = set(
            activity_data['id'] for activity_data in response.data['results']
        )
        assert activity.pk in activities_expected
        assert other_activity.pk not in activities_expected
        assert activities_result == activities_expected

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney',
            # check that shared activity can be retrieved too
            'shared_attorney',
            'support',
        ),
        indirect=True
    )
    def test_retrieve_activity(
        self, api_client: APIClient, user: AppUser, activity: models.Activity,
    ):
        """Test that users can get details of activity."""
        activity.matter.status = models.Matter.STATUS_OPEN
        activity.matter.save()

        url = get_detail_url(activity)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == OK

        models.Activity.objects.available_for_user(user=user).get(
            pk=response.data['id']
        )

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney',
            # check that not shared activity can't be retrieved
            'shared_attorney',
            'support',
        ),
        indirect=True
    )
    def test_retrieve_foreign_activity(
        self, api_client: APIClient, user: AppUser,
        other_activity: models.Activity,
    ):
        """Test that users can't get details of foreign activity."""
        url = get_detail_url(other_activity)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == NOT_FOUND
