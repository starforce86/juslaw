import json

from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import (
    BAD_REQUEST,
    CREATED,
    FORBIDDEN,
    NO_CONTENT,
    NOT_FOUND,
    OK,
    UNAUTHORIZED,
)

from apps.business.models import Matter

from ....business.factories import MatterFactory
from ....users import models as user_models
from ... import factories, models
from ...api import serializers


def get_list_url():
    """Get url for folder creation."""
    return reverse_lazy('v1:folders-list')


def get_detail_url(folder: models.Folder):
    """Get url for folder editing."""
    return reverse_lazy('v1:folders-detail', kwargs={'pk': folder.pk})


def test_non_auth_user_folder_creation(
    api_client: APIClient, private_attorney_folder: models.Folder,
):
    """Check that non-authenticated users can't create folders."""
    api_client.logout()
    folder_json = serializers.FolderSerializer(
        instance=private_attorney_folder
    ).data
    url = get_list_url()

    old_title = folder_json['title']
    folder_json['title'] = f"{old_title}(1)"
    response = api_client.post(url, folder_json)
    assert response.status_code == UNAUTHORIZED


class TestAuthUserAPI:
    """Test folders API for different app users.

    Clients have possibility to view only `shared` folders in his matters.

    Attorneys and support users have possibility:

        - CRUD for private folders
        - CRUD for owned (attorney only) and shared matter folders
        - read admin template folders
        - read own root template folder and create, update, delete nested
        folders inside it.
        - read `shared` matter folders for owned (attorney only) and shared
        matters

    """

    @pytest.mark.parametrize(
        argnames='user, folder, status_code',
        argvalues=(
            # check all folders by client
            ('client', 'private_attorney_folder', NOT_FOUND),
            ('client', 'private_shared_attorney_folder', NOT_FOUND),
            ('client', 'private_support_folder', NOT_FOUND),
            ('client', 'matter_folder', NOT_FOUND),
            ('client', 'other_matter_folder', NOT_FOUND),
            ('client', 'shared_folder', OK),
            ('client', 'other_shared_folder', NOT_FOUND),
            ('client', 'root_admin_template_folder', NOT_FOUND),
            ('client', 'admin_template_folder', NOT_FOUND),
            ('client', 'root_attorney_template_folder', NOT_FOUND),
            ('client', 'attorney_template_folder', NOT_FOUND),
            ('client', 'root_shared_attorney_template_folder', NOT_FOUND),
            ('client', 'shared_attorney_template_folder', NOT_FOUND),
            ('client', 'root_support_template_folder', NOT_FOUND),
            ('client', 'support_template_folder', NOT_FOUND),

            # check all folders by attorney
            ('attorney', 'private_attorney_folder', OK),
            ('attorney', 'private_shared_attorney_folder', NOT_FOUND),
            ('attorney', 'private_support_folder', NOT_FOUND),
            ('attorney', 'matter_folder', OK),
            ('attorney', 'other_matter_folder', NOT_FOUND),
            ('attorney', 'shared_folder', OK),
            ('attorney', 'other_shared_folder', NOT_FOUND),
            ('attorney', 'root_admin_template_folder', OK),
            ('attorney', 'admin_template_folder', OK),
            ('attorney', 'root_attorney_template_folder', OK),
            ('attorney', 'attorney_template_folder', OK),
            ('attorney', 'root_shared_attorney_template_folder', NOT_FOUND),
            ('attorney', 'shared_attorney_template_folder', NOT_FOUND),
            ('attorney', 'root_support_template_folder', NOT_FOUND),
            ('attorney', 'support_template_folder', NOT_FOUND),

            # check all folders by shared attorney
            ('shared_attorney', 'private_attorney_folder', NOT_FOUND),
            ('shared_attorney', 'private_shared_attorney_folder', OK),
            ('shared_attorney', 'private_support_folder', NOT_FOUND),
            ('shared_attorney', 'matter_folder', OK),
            ('shared_attorney', 'other_matter_folder', NOT_FOUND),
            ('shared_attorney', 'shared_folder', OK),
            ('shared_attorney', 'other_shared_folder', NOT_FOUND),
            ('shared_attorney', 'root_admin_template_folder', OK),
            ('shared_attorney', 'admin_template_folder', OK),
            ('shared_attorney', 'root_attorney_template_folder', NOT_FOUND),
            ('shared_attorney', 'attorney_template_folder', NOT_FOUND),
            ('shared_attorney', 'root_shared_attorney_template_folder', OK),
            ('shared_attorney', 'shared_attorney_template_folder', OK),
            ('shared_attorney', 'root_support_template_folder', NOT_FOUND),
            ('shared_attorney', 'support_template_folder', NOT_FOUND),

            # check all folders by support
            ('support', 'private_attorney_folder', NOT_FOUND),
            ('support', 'private_shared_attorney_folder', NOT_FOUND),
            ('support', 'private_support_folder', OK),
            ('support', 'matter_folder', OK),
            ('support', 'other_matter_folder', NOT_FOUND),
            ('support', 'shared_folder', OK),
            ('support', 'other_shared_folder', NOT_FOUND),
            ('support', 'root_admin_template_folder', OK),
            ('support', 'admin_template_folder', OK),
            ('support', 'root_attorney_template_folder', NOT_FOUND),
            ('support', 'attorney_template_folder', NOT_FOUND),
            ('support', 'root_shared_attorney_template_folder', NOT_FOUND),
            ('support', 'shared_attorney_template_folder', NOT_FOUND),
            ('support', 'root_support_template_folder', OK),
            ('support', 'support_template_folder', OK),
        ),
        indirect=True
    )
    def test_retrieve_folder(
        self, api_client: APIClient, folder: models.Folder,
        user: user_models.AppUser, status_code: int
    ):
        """Check retrieve different folders for users."""
        if folder.matter:
            folder.matter.status = Matter.STATUS_OPEN
            folder.matter.save()

        url = get_detail_url(folder)
        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        argnames='user, folder, status_code',
        argvalues=(
            # check all folders by client (clients can work only in `shared`)
            ('client', 'private_attorney_folder', BAD_REQUEST),
            ('client', 'matter_folder', BAD_REQUEST),
            ('client', 'other_matter_folder', BAD_REQUEST),
            ('client', 'shared_folder', BAD_REQUEST),
            ('client', 'other_shared_folder', BAD_REQUEST),
            ('client', 'root_admin_template_folder', BAD_REQUEST),
            ('client', 'admin_template_folder', BAD_REQUEST),
            ('client', 'root_attorney_template_folder', BAD_REQUEST),
            ('client', 'attorney_template_folder', BAD_REQUEST),

            # check all folders by attorney
            ('attorney', 'private_attorney_folder', CREATED),
            ('attorney', 'matter_folder', CREATED),
            ('attorney', 'other_matter_folder', BAD_REQUEST),
            ('attorney', 'shared_folder', CREATED),
            ('attorney', 'other_shared_folder', BAD_REQUEST),
            ('attorney', 'admin_template_folder', BAD_REQUEST),
            ('attorney', 'root_attorney_template_folder', CREATED),
            ('attorney', 'attorney_template_folder', CREATED),

            # check all folders by shared attorney
            ('shared_attorney', 'private_shared_attorney_folder', CREATED),
            ('shared_attorney', 'matter_folder', CREATED),
            ('shared_attorney', 'other_matter_folder', BAD_REQUEST),
            ('shared_attorney', 'shared_folder', CREATED),
            ('shared_attorney', 'other_shared_folder', BAD_REQUEST),
            ('shared_attorney', 'admin_template_folder', BAD_REQUEST),
            ('shared_attorney', 'root_shared_attorney_template_folder', CREATED), # noqa
            ('shared_attorney', 'shared_attorney_template_folder', CREATED),

            # check all folders by support
            ('support', 'private_support_folder', CREATED),
            ('support', 'matter_folder', CREATED),
            ('support', 'other_matter_folder', BAD_REQUEST),
            ('support', 'shared_folder', CREATED),
            ('support', 'other_shared_folder', BAD_REQUEST),
            ('support', 'admin_template_folder', BAD_REQUEST),
            ('support', 'root_support_template_folder', CREATED),
            ('support', 'support_template_folder', CREATED),
        ),
        indirect=True
    )
    def test_create_folder(
        self, api_client: APIClient, folder: models.Folder,
        user: user_models.AppUser, status_code: int
    ):
        """Check api folder creation process for users."""
        if folder.matter:
            folder.matter.status = Matter.STATUS_OPEN
            folder.matter.save()

        folder_json = serializers.FolderSerializer(instance=folder).data
        url = get_list_url()

        old_title = folder_json['title']
        folder_json['title'] = f"{old_title}(1)"
        api_client.force_authenticate(user=user)
        response = api_client.post(url, folder_json)

        assert response.status_code == status_code, response.data

        if response.status_code == CREATED:
            response_data = json.loads(response.content)
            # Check that new folder appeared in db
            models.Folder.objects.get(pk=response_data['id'])

    @pytest.mark.parametrize(
        argnames='user, folder, status_code',
        argvalues=(
            # check all folders by attorney
            ('attorney', 'private_attorney_folder', CREATED),
            ('attorney', 'matter_folder', CREATED),
            ('attorney', 'other_matter_folder', BAD_REQUEST),
            ('attorney', 'shared_folder', BAD_REQUEST),
            ('attorney', 'other_shared_folder', BAD_REQUEST),
            ('attorney', 'admin_template_folder', BAD_REQUEST),
            ('attorney', 'root_attorney_template_folder', CREATED),
            ('attorney', 'attorney_template_folder', CREATED),
            ('attorney', 'support_template_folder', BAD_REQUEST),

            # check all folders by shared attorney
            ('shared_attorney', 'private_shared_attorney_folder', CREATED),
            ('shared_attorney', 'matter_folder', CREATED),
            ('shared_attorney', 'other_matter_folder', BAD_REQUEST),
            ('shared_attorney', 'shared_folder', BAD_REQUEST),
            ('shared_attorney', 'other_shared_folder', BAD_REQUEST),
            ('shared_attorney', 'admin_template_folder', BAD_REQUEST),
            ('shared_attorney', 'root_shared_attorney_template_folder', CREATED), # noqa
            ('shared_attorney', 'shared_attorney_template_folder', CREATED),
            ('shared_attorney', 'attorney_template_folder', BAD_REQUEST),

            # check all folders by support
            ('support', 'private_support_folder', CREATED),
            ('support', 'matter_folder', CREATED),
            ('support', 'other_matter_folder', BAD_REQUEST),
            ('support', 'shared_folder', BAD_REQUEST),
            ('support', 'other_shared_folder', BAD_REQUEST),
            ('support', 'admin_template_folder', BAD_REQUEST),
            ('support', 'root_support_template_folder', CREATED),
            ('support', 'support_template_folder', CREATED),
            ('support', 'attorney_template_folder', BAD_REQUEST),

        ),
        indirect=True
    )
    def test_create_folder_with_parent(
        self, api_client: APIClient, folder: models.Folder,
        user: user_models.AppUser, status_code: int
    ):
        """Check api folder creation in folder for users."""
        if folder.matter:
            folder.matter.status = Matter.STATUS_OPEN
            folder.matter.save()

        folder_json = serializers.FolderSerializer(instance=folder).data
        folder_json['title'] = f"{folder_json['title']}(1)"
        url = get_list_url()
        folder_json['parent'] = folder.pk
        api_client.force_authenticate(user=user)
        response = api_client.post(url, folder_json)

        assert response.status_code == status_code, response.data

        if response.status_code == CREATED:
            response_data = json.loads(response.content)
            # Check that new folder appeared in db
            models.Folder.objects.get(pk=response_data['id'])

    @pytest.mark.parametrize(
        argnames='user, folder',
        argvalues=(
            # check all folders by attorney
            ('attorney', 'private_attorney_folder'),
            ('attorney', 'matter_folder'),
            ('attorney', 'root_attorney_template_folder'),
            ('attorney', 'attorney_template_folder'),

            # check all folders by shared attorney
            ('shared_attorney', 'private_shared_attorney_folder'),
            ('shared_attorney', 'matter_folder'),
            ('shared_attorney', 'root_shared_attorney_template_folder'),
            ('shared_attorney', 'shared_attorney_template_folder'),

            # check all folders by support
            ('support', 'private_support_folder'),
            ('support', 'matter_folder'),
            ('support', 'root_support_template_folder'),
            ('support', 'support_template_folder'),
        ),
        indirect=True
    )
    def test_create_duplicate_folder(
        self, api_client: APIClient, folder: models.Folder,
        user: user_models.AppUser
    ):
        """Check api restrictions for folder creation.

        User can't create duplicate in the same place, without changing
        title.

        """
        folder_json = serializers.FolderSerializer(instance=folder).data
        url = get_list_url()
        api_client.force_authenticate(user=user)
        response = api_client.post(url, folder_json)
        assert response.status_code == BAD_REQUEST

    @pytest.mark.parametrize(
        argnames='user, folder',
        argvalues=(
            # check all folders by client
            ('client', 'shared_folder'),
            ('client', 'root_admin_template_folder'),
            ('client', 'admin_template_folder'),
            ('client', 'root_attorney_template_folder'),

            # check all folders by attorney
            ('attorney', 'shared_folder'),
            ('attorney', 'root_admin_template_folder'),
            ('attorney', 'admin_template_folder'),
            ('attorney', 'root_attorney_template_folder'),

            # check all folders by shared attorney
            ('shared_attorney', 'shared_folder'),
            ('shared_attorney', 'root_admin_template_folder'),
            ('shared_attorney', 'admin_template_folder'),
            ('shared_attorney', 'root_shared_attorney_template_folder'),

            # check all folders by support
            ('support', 'shared_folder'),
            ('support', 'root_admin_template_folder'),
            ('support', 'admin_template_folder'),
            ('support', 'root_support_template_folder'),
        ),
        indirect=True
    )
    def test_folder_editing_forbidden(
        self, api_client: APIClient, folder: models.Folder,
        user: user_models.AppUser
    ):
        """Check that users can't edit shared and main templates folders."""
        if folder.matter:
            folder.matter.status = Matter.STATUS_OPEN
            folder.matter.save()

        folder_json = serializers.FolderSerializer(instance=folder).data
        url = get_detail_url(folder)
        folder_json['title'] = f"{folder_json['title']}(1)"
        api_client.force_authenticate(user=user)
        response = api_client.put(url, folder_json)

        if user.is_client and not folder.is_shared:
            assert response.status_code == NOT_FOUND
            return

        assert response.status_code == FORBIDDEN

    @pytest.mark.parametrize(
        argnames='user, folder',
        argvalues=(
            # check all folders by client
            ('client', 'private_attorney_folder'),
            ('client', 'private_support_folder'),
            ('client', 'private_shared_attorney_folder'),
            ('client', 'matter_folder'),
            ('client', 'attorney_template_folder'),
            ('client', 'support_template_folder'),
            ('client', 'shared_attorney_template_folder'),

            # check all folders by attorney
            ('attorney', 'private_attorney_folder'),
            ('attorney', 'matter_folder'),
            ('attorney', 'attorney_template_folder'),

            # check all folders by shared attorney
            ('shared_attorney', 'private_shared_attorney_folder'),
            ('shared_attorney', 'matter_folder'),
            ('shared_attorney', 'shared_attorney_template_folder'),

            # check all folders by support
            ('support', 'private_support_folder'),
            ('support', 'matter_folder'),
            ('support', 'support_template_folder'),
        ),
        indirect=True
    )
    def test_folder_editing(
        self, api_client: APIClient, folder: models.Folder,
        user: user_models.AppUser
    ):
        """Check logic behind api folder editing process for user.

        Users can edit own private folders, matter's folders, own template
        folders. Clients can't edit anything.

        """
        if folder.matter:
            folder.matter.status = Matter.STATUS_OPEN
            folder.matter.save()

        folder_json = serializers.FolderSerializer(instance=folder).data
        url = get_detail_url(folder)
        folder_json['title'] = f"{folder_json['title']}(1)"
        folder_json['parent'] = factories.FolderFactory(
            matter=folder.matter, owner=user
        ).pk
        folder_json['matter'] = MatterFactory().pk
        folder_json['is_shared'] = not folder.is_shared
        api_client.force_authenticate(user=user)
        response = api_client.put(url, folder_json)

        if user.is_client:
            assert response.status_code == NOT_FOUND
            return

        assert response.status_code == OK
        response_data = json.loads(response.content)
        updated_model = models.Folder.objects.get(pk=response_data['id'])

        # Check that folder was updated in db
        assert updated_model.title == folder_json['title']
        assert updated_model.parent_id == folder_json['parent']

        # Check that read_only fields didn't changed
        assert updated_model.matter == updated_model.matter
        assert updated_model.is_shared == updated_model.is_shared

    @pytest.mark.parametrize(
        argnames='user, folder',
        argvalues=(
            # check all folders by client
            ('client', 'shared_folder'),
            ('client', 'root_admin_template_folder'),
            ('client', 'admin_template_folder'),
            ('client', 'root_attorney_template_folder'),

            # check all folders by attorney
            ('attorney', 'shared_folder'),
            ('attorney', 'root_admin_template_folder'),
            ('attorney', 'admin_template_folder'),
            ('attorney', 'root_attorney_template_folder'),

            # check all folders by shared attorney
            ('shared_attorney', 'shared_folder'),
            ('shared_attorney', 'root_admin_template_folder'),
            ('shared_attorney', 'admin_template_folder'),
            ('shared_attorney', 'root_shared_attorney_template_folder'),

            # check all folders by support
            ('support', 'shared_folder'),
            ('support', 'root_admin_template_folder'),
            ('support', 'admin_template_folder'),
            ('support', 'root_support_template_folder'),
        ),
        indirect=True
    )
    def test_folder_deleting_forbidden(
        self, api_client: APIClient, folder: models.Folder,
        user: user_models.AppUser
    ):
        """Check that users can't edit shared and main templates folders."""
        if folder.matter:
            folder.matter.status = Matter.STATUS_OPEN
            folder.matter.save()

        url = get_detail_url(folder)
        api_client.force_authenticate(user=user)
        response = api_client.delete(url)

        if user.is_client and not folder.is_shared:
            assert response.status_code == NOT_FOUND
            return

        assert response.status_code == FORBIDDEN

    @pytest.mark.parametrize(
        argnames='user, folder',
        argvalues=(
            # check all folders by client
            ('client', 'private_attorney_folder'),
            ('client', 'private_support_folder'),
            ('client', 'private_shared_attorney_folder'),
            ('client', 'matter_folder'),
            ('client', 'attorney_template_folder'),
            ('client', 'support_template_folder'),
            ('client', 'shared_attorney_template_folder'),

            # check all folders by attorney
            ('attorney', 'private_attorney_folder'),
            ('attorney', 'matter_folder'),
            ('attorney', 'attorney_template_folder'),

            # check all folders by shared attorney
            ('shared_attorney', 'private_shared_attorney_folder'),
            ('shared_attorney', 'matter_folder'),
            ('shared_attorney', 'shared_attorney_template_folder'),

            # check all folders by support
            ('support', 'private_support_folder'),
            ('support', 'matter_folder'),
            ('support', 'support_template_folder'),
        ),
        indirect=True
    )
    def test_folder_deleting(
        self, api_client: APIClient, folder: models.Folder,
        user: user_models.AppUser, mocker
    ):
        """Check logic behind api folder deletion process for user.

        Users can delete own private folders, matter's folders, own template
        folders. Clients can't delete any folders.

        """
        if folder.matter:
            folder.matter.status = Matter.STATUS_OPEN
            folder.matter.save()

        delete = mocker.patch('apps.documents.models.Folder.delete')
        url = get_detail_url(folder)
        api_client.force_authenticate(user=user)
        response = api_client.delete(url)

        if user.is_client:
            assert response.status_code == NOT_FOUND
            return

        assert response.status_code == NO_CONTENT
        delete.assert_called()
