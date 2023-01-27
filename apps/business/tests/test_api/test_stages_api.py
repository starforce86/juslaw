from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import (
    CREATED,
    FORBIDDEN,
    NO_CONTENT,
    NOT_FOUND,
    OK,
)

from ....users.models import AppUser, Attorney
from ... import models
from ...api import serializers
from ...factories import StageFactory


def get_list_url():
    """Get url for stage creation and list retrieval."""
    return reverse_lazy('v1:stages-list')


def get_detail_url(stage: models.Stage):
    """Get url for stage editing and retrieval."""
    return reverse_lazy('v1:stages-detail', kwargs={'pk': stage.pk})


@pytest.fixture(scope="module")
def stage(
    django_db_blocker, attorney: Attorney
) -> models.Stage:
    """Create stage for attorney."""
    with django_db_blocker.unblock():
        return StageFactory(attorney=attorney)


@pytest.fixture(scope="module")
def other_stage(django_db_blocker) -> models.Stage:
    """Create other stage for testing."""
    with django_db_blocker.unblock():
        return StageFactory()


class TestAuthUserAPI:
    """Test stage api for auth users.

    Attorney have full CRUD access.
    Client doesn't have access to this api.
    Support can only read related to `shared` matter objects.

    """

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', OK),
            # check for users with which matter is shared
            ('support', OK),
            ('shared_attorney', OK),
        ),
        indirect=True
    )
    def test_get_list_stages(
        self, api_client: APIClient, user: AppUser, status_code: int
    ):
        """Test that attorney and support can get stages, but clients can't."""
        url = get_list_url()
        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status_code

        if status_code != OK:
            return
        stages = models.Stage.objects.filter(attorney_id=user.pk)
        assert stages.count() == response.data['count']
        for stage_data in response.data['results']:
            stages.get(pk=stage_data['id'])

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
    def test_get_list_stages_with_matter(
        self, api_client: APIClient, matter: models.Matter, user: AppUser
    ):
        """Test when `matter` is set - stages of matter's attorney returned
        """
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        api_client.logout()
        api_client.force_authenticate(user=user)

        stage = matter.attorney.stages.first()
        url = f'{get_list_url()}?matter={matter.id}'
        response = api_client.get(url)
        assert response.status_code == OK
        assert stage.id in [i['id'] for i in response.data['results']]

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', OK),
            # check shared attorney and support can't get attorney's
            # checklists without `matter`
            ('support', NOT_FOUND),
            ('shared_attorney', NOT_FOUND),
        ),
        indirect=True
    )
    def test_retrieve_stage(
        self, api_client: APIClient, user: AppUser, stage: models.Stage,
        status_code: int
    ):
        """Test that attorney and support can get stage details, but client not
        """
        url = get_detail_url(stage)
        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status_code

        if status_code == OK:
            models.Stage.objects.filter(attorney_id=user.pk).get(
                pk=response.data['id']
            )

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
    def test_retrieve_stage_with_matter(
        self, api_client: APIClient, user: AppUser,
        matter: models.Matter
    ):
        """Test when `matter` is set - stages of matter's attorney returned
        """
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        api_client.logout()
        api_client.force_authenticate(user=user)

        stage = matter.attorney.stages.first()
        url = f'{get_detail_url(stage)}?matter={matter.id}'
        response = api_client.get(url)
        assert response.status_code == OK
        assert response.data['id'] == stage.id

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', CREATED),
            # shared attorney can create own stages
            ('shared_attorney', CREATED),
            # support can't create own stages
            ('support', FORBIDDEN),
        ),
        indirect=True
    )
    def test_create_stage(
        self, api_client: APIClient, user: AppUser, stage: models.Stage,
        status_code: int
    ):
        """Test that attorney can create stage, but client and support not."""
        stage_json = serializers.StageSerializer(instance=stage).data
        url = get_list_url()
        api_client.force_authenticate(user=user)
        response = api_client.post(url, stage_json)

        assert response.status_code == status_code

        if status_code == CREATED:
            # Check that new stage appeared in db
            models.Stage.objects.filter(attorney_id=user.pk).get(
                pk=response.data['id']
            )

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', OK),
            # shared attorney can't update foreign stages
            ('shared_attorney', NOT_FOUND),
            # support can't update own stages
            ('support', FORBIDDEN),
        ),
        indirect=True
    )
    def test_edit_stage(
        self, api_client: APIClient, user: AppUser, stage: models.Stage,
        status_code: int
    ):
        """Test that attorney can stage, but client can't."""
        stage_json = serializers.StageSerializer(instance=stage).data
        title = 'test stage editing'
        stage_json['title'] = title
        url = get_detail_url(stage)
        api_client.force_authenticate(user=user)
        response = api_client.put(url, stage_json)

        assert response.status_code == status_code

        if status_code == OK:
            # Check that stage was updated in db
            stage.refresh_from_db()
            assert stage.title == title

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('attorney', OK),
            # shared attorney and matter
            ('shared_attorney', NOT_FOUND),
            ('support', FORBIDDEN)
        ),
        indirect=True
    )
    def test_edit_stage_with_shared_matter(
        self, api_client: APIClient, attorney: Attorney,
        matter: models.Matter, user: AppUser, status_code: int
    ):
        """Test users can't edit stages of other user even for shared `matter`.
        """
        api_client.logout()
        api_client.force_authenticate(user=user)

        stage = matter.attorney.stages.first()
        stage_json = serializers.StageSerializer(instance=stage).data
        url = f'{get_detail_url(stage)}?matter={matter.id}'
        response = api_client.put(url, stage_json)
        assert response.status_code == status_code

    def test_edit_foreign_stage(
        self, auth_attorney_api: APIClient, other_stage: models.Stage
    ):
        """Test that users can't edit stage entry of other user."""
        checklist_entry_json = serializers.StageSerializer(
            instance=other_stage
        ).data
        url = get_detail_url(other_stage)
        response = auth_attorney_api.put(url, checklist_entry_json)
        assert response.status_code == NOT_FOUND

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', NO_CONTENT),
            # shared attorney can't delete foreign stages
            ('shared_attorney', NOT_FOUND),
            # shared support can't delete stages
            ('support', FORBIDDEN),
        ),
        indirect=True
    )
    def test_delete_stage(
        self, api_client: APIClient, user: AppUser, attorney: Attorney,
        status_code: int
    ):
        """Test that attorney can delete stage, but clients and support can't.
        """
        url = get_detail_url(StageFactory(attorney=attorney))
        api_client.force_authenticate(user=user)
        response = api_client.delete(url)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('attorney', NO_CONTENT),
            # shared attorney and matter
            ('shared_attorney', NOT_FOUND),
            ('support', FORBIDDEN)
        ),
        indirect=True
    )
    def test_delete_foreign_stage_with_matter(
        self, api_client: APIClient, attorney: Attorney, user: AppUser,
        status_code: int, matter: models.Matter
    ):
        """Test users can't delete stage of other user even for shared `matter`
        """
        api_client.logout()
        api_client.force_authenticate(user=user)

        stage = attorney.stages.first()
        url = f'{get_detail_url(stage)}?matter={matter.id}'
        response = api_client.delete(url)
        assert response.status_code == status_code

    def test_delete_foreign_stage(
        self, auth_attorney_api: APIClient, other_stage: models.Stage
    ):
        """Test that users can't delete stage of other user."""
        url = get_detail_url(other_stage)
        response = auth_attorney_api.delete(url)
        assert response.status_code == NOT_FOUND
