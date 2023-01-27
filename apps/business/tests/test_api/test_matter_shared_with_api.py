from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import NOT_FOUND, OK

from ....users.models import AppUser
from ... import factories, models


def get_list_url():
    """Get url for matter_shared_with list retrieval."""
    return reverse_lazy('v1:matter-shared-with-list')


def get_detail_url(matter_shared_with: models.MatterSharedWith):
    """Get url for matter_shared_with retrieval."""
    return reverse_lazy(
        'v1:matter-shared-with-detail', kwargs={'pk': matter_shared_with.pk}
    )


@pytest.fixture(scope='module')
def other_shared_matter(django_db_blocker) -> models.MatterSharedWith:
    """Create other shared matter for testing."""
    with django_db_blocker.unblock():
        return factories.MatterSharedWithFactory()


class TestAuthUserAPI:
    """Test matter_shared_with api for auth users.

    Client can get matter_shared_with from its related matters.
    Attorneys can get matter_shared_with from their own matters or
    shared with them matters.
    Support can get matter_shared_with from shared with them matters.

    """

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney',
            'shared_attorney',
            'support',
        ),
        indirect=True
    )
    def test_get_list_matter_shared_with(
        self, api_client: APIClient, user: AppUser,
        shared_matter: models.MatterSharedWith,
        other_shared_matter: models.MatterSharedWith
    ):
        """Test that users can get list of shared matters."""
        shared_matter.matter.status = models.Matter.STATUS_OPEN
        shared_matter.matter.save()

        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == OK

        shared_matters_expected = set(
            models.MatterSharedWith.objects.available_for_user(
                user=user
            ).values_list(
                'pk', flat=True
            )
        )
        shared_matters_result = set(
            matter_shared_with_data['id']
            for matter_shared_with_data in response.data['results']
        )
        assert shared_matter.pk in shared_matters_result
        assert other_shared_matter.pk not in shared_matters_result
        assert shared_matters_result == shared_matters_expected

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney',
            'shared_attorney',
            'support',
        ),
        indirect=True
    )
    def test_retrieve_matter_shared_with(
        self,
        api_client: APIClient,
        user: AppUser,
        shared_matter: models.MatterSharedWith,
    ):
        """Test that users can get details of shared_matter."""
        shared_matter.matter.status = models.Matter.STATUS_OPEN
        shared_matter.matter.save()

        url = get_detail_url(shared_matter)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == OK

        models.MatterSharedWith.objects.available_for_user(user=user).get(
            pk=response.data['id']
        )

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney',
            'shared_attorney',
            'support',
        ),
        indirect=True
    )
    def test_retrieve_foreign_matter_shared_with(
        self, api_client: APIClient, user: AppUser,
        other_shared_matter: models.MatterSharedWith,
    ):
        """Test that users can't get details of foreign shared_matter."""
        url = get_detail_url(other_shared_matter)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == NOT_FOUND
