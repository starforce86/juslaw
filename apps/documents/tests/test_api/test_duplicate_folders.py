import json

from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import BAD_REQUEST, CREATED, FORBIDDEN, NOT_FOUND

from apps.business.models import Matter

from ....users.models import AppUser
from ... import factories, models
from ...api import serializers


def get_duplicate_folder_url(folder: models.Folder):
    """Get url for folder duplicating."""
    return reverse_lazy('v1:folders-duplicate', kwargs={'pk': folder.pk})


def check_duplicated(
    duplicate: models.Folder,
    original: models.Folder,
    new_folder: models.Folder = None
):
    """Check that folder was copied correctly."""
    if new_folder:
        assert duplicate.parent_id == new_folder.pk
    assert duplicate.matter_id == original.matter_id
    # Check that all documents duplicated with out errors
    docs_zip = zip(
        original.documents.all().order_by('title'),
        duplicate.documents.all().order_by('title')
    )
    for original_document, duplicate_document in docs_zip:
        assert original_document.title == duplicate_document.title
        assert original_document.file == duplicate_document.file
        assert original_document.matter_id == duplicate_document.matter_id
        assert original_document.owner_id == duplicate_document.owner_id
        assert original_document.parent_id != duplicate_document.parent_id


class TestClientAPI:
    """Test duplicate feature for client."""

    @pytest.mark.parametrize(
        argnames='folder, status_code',
        argvalues=(
            ('private_attorney_folder', NOT_FOUND),
            ('private_shared_attorney_folder', NOT_FOUND),
            ('private_support_folder', NOT_FOUND),
            ('matter_folder', NOT_FOUND),
            ('other_matter_folder', NOT_FOUND),
            ('shared_folder', FORBIDDEN),
            ('other_shared_folder', NOT_FOUND),
            ('root_admin_template_folder', NOT_FOUND),
            ('admin_template_folder', NOT_FOUND),
            ('root_attorney_template_folder', NOT_FOUND),
            ('attorney_template_folder', NOT_FOUND),
            ('root_shared_attorney_template_folder', NOT_FOUND),
            ('shared_attorney_template_folder', NOT_FOUND),
            ('root_support_template_folder', NOT_FOUND),
            ('support_template_folder', NOT_FOUND),
        ),
        indirect=True
    )
    def test_folder_duplicate_client_restriction(
        self, auth_client_api: APIClient, folder: models.Folder,
        status_code: int,
    ):
        """Client doesn't have access to matter and template folders.

        Client can't duplicate matter, shared and template folders.

        """
        folder_json = serializers.FolderSerializer(instance=folder).data
        url = get_duplicate_folder_url(folder)

        response = auth_client_api.post(url, folder_json)
        assert response.status_code == status_code


class TestAttorneySupportAPI:
    """Test duplicate feature for attorney and support users."""

    @pytest.mark.parametrize(
        argnames='user, folder',
        argvalues=(
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
    def test_folder_duplicate_unique_restriction(
        self, api_client: APIClient, user: AppUser, folder: models.Folder
    ):
        """We can't create duplicate without changing title or parent."""
        if folder.matter:
            folder.matter.status = Matter.STATUS_OPEN
            folder.matter.save()

        folder_json = serializers.FolderSerializer(instance=folder).data
        url = get_duplicate_folder_url(folder)

        api_client.force_authenticate(user=user)
        response = api_client.post(url, folder_json)
        assert response.status_code == BAD_REQUEST

        # Test the same, but all params are None
        response = api_client.post(
            url, {'title': None, 'parent': None}, format='json'
        )
        assert response.status_code == BAD_REQUEST

    @pytest.mark.parametrize(
        argnames='user, folder',
        argvalues=(
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
    def test_folder_duplicate_folders_restriction(
        self, api_client: APIClient, user: AppUser, folder: models.Folder
    ):
        """Test that we can't create duplicate of shared folders."""
        if folder.matter:
            folder.matter.status = Matter.STATUS_OPEN
            folder.matter.save()

        folder_json = serializers.FolderSerializer(instance=folder).data
        url = get_duplicate_folder_url(folder)
        api_client.force_authenticate(user=user)
        response = api_client.post(url, folder_json)
        assert response.status_code == FORBIDDEN

    @pytest.mark.parametrize(
        argnames='user, folder',
        argvalues=(
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
    def test_folder_duplicate_with_title(
        self, api_client: APIClient, user: AppUser, folder: models.Folder
    ):
        """Test duplication on folder with different title."""
        if folder.matter:
            folder.matter.status = Matter.STATUS_OPEN
            folder.matter.save()

        folder_json = serializers.FolderSerializer(instance=folder).data
        url = get_duplicate_folder_url(folder)

        folder_json['title'] = f'{folder.title}(1)'
        api_client.force_authenticate(user=user)
        response = api_client.post(url, folder_json)
        assert response.status_code == CREATED
        response_data = json.loads(response.content)

        # Check that data of duplicated folder in db
        duplicate = models.Folder.objects.get(pk=response_data['id'])
        assert duplicate.title == folder_json['title']
        assert duplicate.is_shared == folder.is_shared
        check_duplicated(duplicate, folder)

    @pytest.mark.parametrize(
        argnames='user, folder',
        argvalues=(
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
    def test_folder_duplicate_with_parent(
        self, api_client: APIClient, user: AppUser, folder: models.Folder
    ):
        """Test duplication on folder with different parent."""
        if folder.matter:
            folder.matter.status = Matter.STATUS_OPEN
            folder.matter.save()

        folder_json = serializers.FolderSerializer(instance=folder).data
        url = get_duplicate_folder_url(folder)

        new_folder = factories.FolderFactory(
            owner=folder.owner,
            matter=folder.matter,
            parent=folder.parent
        )
        folder_json['parent'] = new_folder.pk
        api_client.force_authenticate(user=user)
        response = api_client.post(url, folder_json)
        assert response.status_code == CREATED
        response_data = json.loads(response.content)

        # Check that data of duplicated folder in db
        duplicate = models.Folder.objects.get(pk=response_data['id'])
        assert duplicate.title == folder.title
        assert duplicate.is_shared == folder.is_shared
        check_duplicated(duplicate, folder, new_folder)
