from django.urls import reverse_lazy

from rest_framework.test import APIClient

import arrow
import pytest

from libs.testing.constants import (
    BAD_REQUEST,
    CREATED,
    FORBIDDEN,
    NOT_FOUND,
    OK,
)

from apps.users.factories import AttorneyVerifiedFactory

from ....users.models import AppUser, Attorney
from ... import models
from ...api import serializers
from ...factories import StageFactory


@pytest.fixture
def matter_status(request) -> int:
    """Fixture to parametrize matter_statuses."""
    return request.param


def get_list_url():
    """Get url for matter creation and list retrieval."""
    return reverse_lazy('v1:matters-list')


def get_detail_url(matter: models.Matter):
    """Get url for matter editing and retrieval."""
    return reverse_lazy('v1:matters-detail', kwargs={'pk': matter.pk})


def get_status_change_url(matter: models.Matter, status_method: str):
    """Get url for matter status change."""
    return reverse_lazy(
        f'v1:matters-{status_method}', kwargs={'pk': matter.pk}
    )


def get_share_url(matter: models.Matter):
    """Get url for matter `share`."""
    return reverse_lazy(
        'v1:matters-share-with', kwargs={'pk': matter.pk}
    )


@pytest.fixture(scope='module')
def stage(django_db_blocker, attorney: Attorney) -> models.Activity:
    """Create stage for testing."""
    with django_db_blocker.unblock():
        return StageFactory(attorney=attorney)


def serialize_matter(matter: models.Matter, user: AppUser) -> dict:
    """Create json from matter."""
    data = serializers.MatterSerializer(instance=matter).data
    data['code'] = user.full_name
    return data


class TestAuthUserAPI:
    """Test matters api for auth users.

    Clients have only read access to related matters.
    Attorneys have full CRUD access to owned and shared with them matters.
    Support have almost full access to matter's API for shared with them
    matters except possibility to `create` new ones.

    """

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_get_list_matters(
        self, api_client: APIClient, user: AppUser, matter: models.Matter
    ):
        """Test that users can get list of matters."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        url = get_list_url()
        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == OK

        matters_expected = set(
            models.Matter.objects.available_for_user(
                user=user
            ).values_list(
                'pk', flat=True
            )
        )
        matters_result = set(
            matter_data['id'] for matter_data in response.data['results']
        )
        assert matter.pk in matters_result
        assert matters_result == matters_expected

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_retrieve_matters(
        self, api_client: APIClient, user: AppUser, matter: models.Matter
    ):
        """Test that users can get details of matter."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        url = get_detail_url(matter)
        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == OK

        models.Matter.objects.available_for_user(user=user).get(
            pk=response.data['id']
        )

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_retrieve_foreign_matters(
        self, api_client: APIClient, user: AppUser,
        another_matter: models.Matter
    ):
        """Test that users can't get details of foreign matter."""
        url = get_detail_url(another_matter)
        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == NOT_FOUND

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', CREATED),
            # shared attorneys can create own matters
            ('shared_attorney', CREATED),
            # shared support can't create own matters
            ('support', FORBIDDEN),
        ),
        indirect=True
    )
    def test_create_matter(
        self, api_client: APIClient, matter: models.Matter, user: AppUser,
        status_code: int
    ):
        """Test that attorneys only can create matter."""
        data = serialize_matter(matter=matter, user=user)
        data['lead'] = None
        data['stage'] = None

        url = get_list_url()
        api_client.force_authenticate(user=user)
        response = api_client.post(url, data)

        assert response.status_code == status_code, response.data

        if response.status_code == CREATED:
            # Check that new matter appeared in db
            models.Matter.objects.get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', OK),
            # shared attorneys and support
            ('shared_attorney', OK),
            ('support', OK),
        ),
        indirect=True
    )
    def test_edit_matter(
        self, api_client: APIClient, matter: models.Matter, user: AppUser,
        status_code: int
    ):
        """Test that users can edit matters."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        data = serializers.UpdateMatterSerializer(instance=matter).data
        url = get_detail_url(matter)
        api_client.force_authenticate(user=user)
        response = api_client.put(url, data)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        argnames='user, matter_status, status_code',
        argvalues=(
            # check draft status
            ('attorney', models.Matter.STATUS_OPEN, OK),
            # check for users with which matter is shared
            ('shared_attorney', models.Matter.STATUS_OPEN, NOT_FOUND),
            ('support', models.Matter.STATUS_OPEN, NOT_FOUND),

            # check pending status
            ('attorney', models.Matter.STATUS_OPEN, OK),
            # check for users with which matter is shared
            ('shared_attorney', models.Matter.STATUS_OPEN, NOT_FOUND),
            ('support', models.Matter.STATUS_OPEN, NOT_FOUND),
        ),
        indirect=True
    )
    def test_edit_pending_or_draft_matter(
        self, api_client: APIClient, matter: models.Matter, user: AppUser,
        matter_status: str, status_code
    ):
        """Test that only attorney can edit matter when it's pending or draft.

        Fields that can be edited when matter is pending or draft:

            * stage
            * city
            * state
            * country
            * rate
            * rate_type
            * title
            * description
            * code

        """
        matter.status = matter_status
        matter.title = 'Test'
        matter.save()

        data = serializers.UpdateMatterSerializer(instance=matter).data
        data['title'] = 'Test updated'

        url = get_detail_url(matter)
        api_client.force_authenticate(user=user)
        response = api_client.put(url, data)
        assert response.status_code == status_code

        if status_code == OK:
            matter.refresh_from_db()
            assert matter.title == data['title']

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_edit_not_pending_or_draft_matter(
        self, api_client: APIClient, matter: models.Matter,
        stage: models.Stage, user: AppUser
    ):
        """Test that user can edit matter when it's not pending or draft.

        When matter is not pending or draft user can only edit stage.

        """
        matter.status = models.Matter.STATUS_OPEN
        matter.title = 'Test'
        matter.save()

        data = serializers.UpdateMatterSerializer(instance=matter).data
        data['stage'] = stage.pk
        data['title'] = 'Test updated'
        url = get_detail_url(matter)

        api_client.force_authenticate(user=user)
        response = api_client.put(url, data)
        assert response.status_code == OK

        # Check that matter's data was updated correctly
        matter.refresh_from_db()
        assert matter.stage == stage
        assert matter.title != data['title']

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_edit_foreign_matter(
        self, api_client: APIClient, another_matter: models.Matter,
        user: AppUser
    ):
        """Test that user can't edit matter of another attorney."""
        api_client.force_authenticate(user=user)
        response = api_client.put(get_detail_url(another_matter))
        assert response.status_code == NOT_FOUND

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', OK),
            # shared attorneys and support
            ('shared_attorney', OK),
            ('support', OK),
        ),
        indirect=True
    )
    def test_change_status(
        self, api_client: APIClient, matter: models.Matter, user: AppUser,
        status_code: int
    ):
        """Test that user can change status of matter."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        url = get_status_change_url(matter, status_method='revoke')
        api_client.force_authenticate(user=user)
        response = api_client.post(url)
        assert response.status_code == status_code

        if response.status_code == OK:
            # Check that matter's status was updated correctly
            matter.refresh_from_db()
            assert matter.status == models.Matter.STATUS_REVOKED
            # check that last activity is created by `attorney` user
            assert user.display_name in matter.activities.last().title

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_change_status_foreign_matter(
        self, api_client: APIClient, another_matter: models.Matter,
        user: AppUser
    ):
        """Test that user can't change status of foreign matter."""
        api_client.force_authenticate(user=user)
        url = get_status_change_url(another_matter, status_method='revoke')
        response = api_client.post(url)
        assert response.status_code == NOT_FOUND

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_change_incorrect_status(
        self, api_client: APIClient, matter: models.Matter, user: AppUser
    ):
        """Test that user can't change status to incorrect.

        Check that api method catches django fcm transition errors and returns
        403 status

        """
        matter.status = models.Matter.STATUS_COMPLETED
        matter.save()

        url = get_status_change_url(matter, status_method='revoke')
        api_client.force_authenticate(user=user)
        response = api_client.post(url)
        assert response.status_code == FORBIDDEN

        # Check that matter's status wasn't changed
        matter.refresh_from_db()
        assert matter.status != models.Matter.STATUS_REVOKED
        assert matter.status == models.Matter.STATUS_COMPLETED

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_complete_matter_status(
        self, api_client: APIClient, matter: models.Matter, user: AppUser
    ):
        """Test that attorney can complete matter and set complete date."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        completed = arrow.now()
        complete_json = {
            'completed': completed.isoformat()
        }
        url = get_status_change_url(matter, status_method='complete')
        api_client.force_authenticate(user=user)
        response = api_client.post(url, complete_json)
        assert response.status_code == OK

        # Check that matter's data was updated correctly
        matter.refresh_from_db()
        assert matter.status == models.Matter.STATUS_COMPLETED
        assert matter.completed == completed.datetime

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'other_attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_complete_foreign_matter_status(
        self, api_client: APIClient, another_matter: models.Matter,
        user: AppUser
    ):
        """Test that a user can't complete foreign matters."""
        another_matter.status = models.Matter.STATUS_OPEN
        another_matter.save()

        completed = arrow.now()
        complete_json = {
            'completed': completed.isoformat()
        }
        url = get_status_change_url(another_matter, status_method='complete')
        api_client.force_authenticate(user=user)
        response = api_client.post(url, complete_json)
        assert response.status_code == NOT_FOUND, response.data

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', OK),
            # shared attorneys and support
            ('shared_attorney', OK),
            ('support', OK),
        ),
        indirect=True
    )
    def test_share_matter(
        self, api_client: APIClient, matter: models.Matter, user: AppUser,
        status_code: int
    ):
        """Test that user can `share` matter."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        # check that matter has no invitations for required email yet
        invitation_email = 'share-matter@test.com'
        assert not matter.invitations.filter(
            email=invitation_email,
            inviter=matter.attorney.user
        ).exists()

        another_attorney = AttorneyVerifiedFactory()
        params = {
            'title': 'Test',
            'message': 'Test',
            'users': [another_attorney.user.pk],
            'emails': [invitation_email]
        }
        api_client.force_authenticate(user=user)
        response = api_client.post(get_share_url(matter), params)

        assert response.status_code == status_code

        if response.status_code == OK:
            assert len(response.data['shared_with']) == 2
            assert another_attorney.user.id in response.data['shared_with']
            # check that invitation is created
            assert matter.invitations.filter(
                email=invitation_email,
                inviter=user
            ).exists()

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_share_foreign_matter(
        self, api_client: APIClient, another_matter: models.Matter,
        user: AppUser
    ):
        """Test that attorney can't `share` owned by another attorney matter.
        """
        api_client.force_authenticate(user=user)
        response = api_client.post(get_share_url(another_matter))
        assert response.status_code == NOT_FOUND

    def test_share_matter_with_existing_emails(
        self, auth_attorney_api: APIClient, matter: models.Matter
    ):
        """Test error is raised when user shares matter with existing emails.
        """
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        params = {
            'title': 'Test',
            'message': 'Test',
            'emails': [matter.attorney.email]
        }
        response = auth_attorney_api.post(get_share_url(matter), params)
        assert response.status_code == BAD_REQUEST

    @pytest.mark.parametrize(
        argnames='matter_status,',
        argvalues=(
            models.Matter.STATUS_OPEN,
        ),
    )
    def test_share_matter_wrong_status(
        self,
        auth_attorney_api: APIClient,
        matter: models.Matter,
        matter_status: str
    ):
        """Test that user can't `share` matter in a wrong status."""
        matter.status = matter_status
        matter.save()
        response = auth_attorney_api.post(get_share_url(matter))
        assert response.status_code == BAD_REQUEST
