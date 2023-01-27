import json

from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from libs.testing.constants import (
    BAD_REQUEST,
    CREATED,
    NO_CONTENT,
    NOT_FOUND,
    OK,
)

from apps.business.models import Matter

from ....users import models as user_models
from ... import factories, models
from ...api import serializers


def get_list_url():
    """Get url for document creation."""
    return reverse_lazy('v1:documents-list')


def get_detail_url(document: models.Document):
    """Get url for document editing."""
    return reverse_lazy('v1:documents-detail', kwargs={'pk': document.pk})


def serialize_document(document: models.Document) -> dict:
    """Serialize document instance."""
    document_json = serializers.DocumentSerializer(
        instance=document
    ).data
    document_json['file'] = f'http://localhost{document.file.url}'
    return document_json


def test_non_auth_user_document_creation(
    api_client: APIClient, private_attorney_document: models.Document,
):
    """Check that non-authenticated users can't create documents."""
    api_client.logout()
    document_json = serialize_document(private_attorney_document)
    url = get_list_url()

    old_title = document_json['title']
    document_json['title'] = f"{old_title}(1)"
    response = api_client.post(url, document_json)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestClientAPI:
    """Test documents api for client."""

    @pytest.mark.parametrize(
        argnames='document, status_code',
        argvalues=(
            ('private_attorney_document', NOT_FOUND),
            ('private_shared_attorney_document', NOT_FOUND),
            ('private_support_document', NOT_FOUND),
            ('matter_document', NOT_FOUND),
            ('shared_document', OK),
            ('other_matter_document', NOT_FOUND),
            ('other_shared_document', NOT_FOUND),
            ('admin_template_document', NOT_FOUND),
            ('attorney_template_document', NOT_FOUND),
            ('shared_attorney_template_document', NOT_FOUND),
            ('support_template_document', NOT_FOUND),
        ),
        indirect=True
    )
    def test_retrieve_document(
        self, auth_client_api: APIClient, document: models.Document,
        status_code: int
    ):
        """Check logic behind api document creation process for client.

        Client can only create documents in shared folder

        """
        url = get_detail_url(document)
        response = auth_client_api.get(url)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        argnames='document, status_code',
        argvalues=(
            ('private_attorney_document', BAD_REQUEST),
            ('private_shared_attorney_document', BAD_REQUEST),
            ('private_support_document', BAD_REQUEST),
            ('matter_document', BAD_REQUEST),
            ('shared_document', CREATED),
            ('other_matter_document', BAD_REQUEST),
            ('other_shared_document', BAD_REQUEST),
            ('admin_template_document', BAD_REQUEST),
            ('attorney_template_document', BAD_REQUEST),
            ('shared_attorney_template_document', BAD_REQUEST),
            ('support_template_document', BAD_REQUEST),
        ),
        indirect=True
    )
    def test_document_creation(
        self, auth_client_api: APIClient, document: models.Document,
        status_code: int
    ):
        """Check logic behind api document creation process for client.

        Client can only create documents in shared folder

        """
        document_json = serialize_document(document)
        url = get_list_url()
        old_title = document_json['title']
        document_json['title'] = f'{old_title}(1)'

        response = auth_client_api.post(url, document_json)
        assert response.status_code == status_code

        if response.status_code == CREATED:
            response_data = json.loads(response.content)
            # Check that new document appeared in db
            models.Document.objects.get(pk=response_data['id'])

    @pytest.mark.parametrize(
        argnames='document, status_code',
        argvalues=(
            ('private_attorney_document', NOT_FOUND),
            ('private_shared_attorney_document', NOT_FOUND),
            ('private_support_document', NOT_FOUND),
            ('matter_document', NOT_FOUND),
            ('shared_document', OK),
            ('other_matter_document', NOT_FOUND),
            ('other_shared_document', NOT_FOUND),
            ('admin_template_document', NOT_FOUND),
            ('attorney_template_document', NOT_FOUND),
            ('shared_attorney_template_document', NOT_FOUND),
            ('support_template_document', NOT_FOUND),
        ),
        indirect=True
    )
    def test_document_editing(
        self, auth_client_api: APIClient, document: models.Document,
        status_code: int
    ):
        """Check logic behind api document editing process for client.

        Client can only access documents in shared folder.

        """
        document_json = serialize_document(document)
        url = get_detail_url(document)
        document_json['title'] = f"{document_json['title']}(1)"
        response = auth_client_api.put(url, document_json)
        assert response.status_code == status_code, response.data

    @pytest.mark.parametrize(
        argnames='document, status_code',
        argvalues=(
            ('private_attorney_document', NOT_FOUND),
            ('private_shared_attorney_document', NOT_FOUND),
            ('private_support_document', NOT_FOUND),
            ('matter_document', NOT_FOUND),
            ('shared_document', NO_CONTENT),
            ('other_matter_document', NOT_FOUND),
            ('other_shared_document', NOT_FOUND),
            ('admin_template_document', NOT_FOUND),
            ('attorney_template_document', NOT_FOUND),
            ('shared_attorney_template_document', NOT_FOUND),
            ('support_template_document', NOT_FOUND),
        ),
        indirect=True
    )
    def test_document_deletion(
        self, auth_client_api: APIClient, document: models.Document,
        status_code: int, mocker
    ):
        """Check logic behind api document deletion process for client.

        Client can only access documents in shared folder.

        """
        delete = mocker.patch('apps.documents.models.Document.delete')
        url = get_detail_url(document)
        response = auth_client_api.delete(url)
        assert response.status_code == status_code

        if response.status_code == NO_CONTENT:
            delete.assert_called()


class TestAttorneySupportAPI:
    """Test documents api for attorney and support."""

    @pytest.mark.parametrize(
        argnames='user, document, status_code',
        argvalues=(
            # check all document by attorney
            ('attorney', 'private_attorney_document', OK),
            ('attorney', 'private_shared_attorney_document', NOT_FOUND),
            ('attorney', 'private_support_document', NOT_FOUND),
            ('attorney', 'matter_document', OK),
            ('attorney', 'other_matter_document', NOT_FOUND),
            ('attorney', 'shared_document', OK),
            ('attorney', 'other_shared_document', NOT_FOUND),
            ('attorney', 'admin_template_document', OK),
            ('attorney', 'attorney_template_document', OK),
            ('attorney', 'shared_attorney_template_document', NOT_FOUND),
            ('attorney', 'support_template_document', NOT_FOUND),

            # check all document by shared attorney
            ('shared_attorney', 'private_attorney_document', NOT_FOUND),
            ('shared_attorney', 'private_shared_attorney_document', OK),
            ('shared_attorney', 'private_support_document', NOT_FOUND),
            ('shared_attorney', 'matter_document', OK),
            ('shared_attorney', 'other_matter_document', NOT_FOUND),
            ('shared_attorney', 'shared_document', OK),
            ('shared_attorney', 'other_shared_document', NOT_FOUND),
            ('shared_attorney', 'admin_template_document', OK),
            ('shared_attorney', 'attorney_template_document', NOT_FOUND),
            ('shared_attorney', 'shared_attorney_template_document', OK),
            ('shared_attorney', 'support_template_document', NOT_FOUND),

            # check all document by support
            ('support', 'private_attorney_document', NOT_FOUND),
            ('support', 'private_shared_attorney_document', NOT_FOUND),
            ('support', 'private_support_document', OK),
            ('support', 'matter_document', OK),
            ('support', 'other_matter_document', NOT_FOUND),
            ('support', 'shared_document', OK),
            ('support', 'other_shared_document', NOT_FOUND),
            ('support', 'admin_template_document', OK),
            ('support', 'attorney_template_document', NOT_FOUND),
            ('support', 'shared_attorney_template_document', NOT_FOUND),
            ('support', 'support_template_document', OK),
        ),
        indirect=True
    )
    def test_retrieve_document(
        self, api_client: APIClient, document: models.Document,
        user: user_models.AppUser, status_code: int
    ):
        """Check retrieve different documents for users."""
        if document.matter:
            document.matter.status = Matter.STATUS_OPEN
            document.matter.save()

        url = get_detail_url(document)
        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        argnames='user, document, status_code',
        argvalues=(
            # check all documents by attorney
            ('attorney', 'private_attorney_document', CREATED),
            ('attorney', 'matter_document', CREATED),
            ('attorney', 'shared_document', CREATED),
            ('attorney', 'other_matter_document', BAD_REQUEST),
            ('attorney', 'other_shared_document', BAD_REQUEST),
            ('attorney', 'admin_template_document', BAD_REQUEST),
            ('attorney', 'attorney_template_document', CREATED),
            ('attorney', 'support_template_document', BAD_REQUEST),

            # check all documents by shared attorney
            ('shared_attorney', 'private_shared_attorney_document', CREATED),
            ('shared_attorney', 'matter_document', CREATED),
            ('shared_attorney', 'shared_document', CREATED),
            ('shared_attorney', 'other_matter_document', BAD_REQUEST),
            ('shared_attorney', 'other_shared_document', BAD_REQUEST),
            ('shared_attorney', 'admin_template_document', BAD_REQUEST),
            ('shared_attorney', 'shared_attorney_template_document', CREATED),
            ('shared_attorney', 'support_template_document', BAD_REQUEST),

            # check all documents by attorney
            ('support', 'private_support_document', CREATED),
            ('support', 'matter_document', CREATED),
            ('support', 'shared_document', CREATED),
            ('support', 'other_matter_document', BAD_REQUEST),
            ('support', 'other_shared_document', BAD_REQUEST),
            ('support', 'admin_template_document', BAD_REQUEST),
            ('support', 'support_template_document', CREATED),
            ('support', 'attorney_template_document', BAD_REQUEST),
        ),
        indirect=True
    )
    def test_document_creation_with_different_name(
        self, api_client: APIClient, document: models.Document,
        user: user_models.AppUser, status_code: int
    ):
        """Check logic behind api document creation process."""
        if document.matter:
            document.matter.status = Matter.STATUS_OPEN
            document.matter.save()

        document_json = serialize_document(document)
        url = get_list_url()
        document_json['title'] = f"{document_json['title']}(1)"
        api_client.force_authenticate(user=user)
        response = api_client.post(url, document_json)

        assert response.status_code == status_code, response.data

        if response.status_code == CREATED:
            response_data = json.loads(response.content)
            # Check that new folder appeared in db
            models.Document.objects.get(pk=response_data['id'])

    @pytest.mark.parametrize(
        argnames='user, document',
        argvalues=(
            # check all cases by attorney
            ('attorney', 'private_attorney_document'),
            ('attorney', 'matter_document'),
            ('attorney', 'shared_document'),
            ('attorney', 'attorney_template_document'),

            # check all cases by shared attorney
            ('shared_attorney', 'private_shared_attorney_document'),
            ('shared_attorney', 'matter_document'),
            ('shared_attorney', 'shared_document'),
            ('shared_attorney', 'shared_attorney_template_document'),

            # check all cases by support
            ('support', 'private_support_document'),
            ('support', 'matter_document'),
            ('support', 'shared_document'),
            ('support', 'support_template_document'),
        ),
        indirect=True
    )
    def test_document_creation_with_same_name(
        self, api_client: APIClient, document: models.Document,
        user: user_models.AppUser
    ):
        """Check logic behind api document creation process."""
        document_json = serialize_document(document)
        url = get_list_url()
        api_client.force_authenticate(user=user)
        response = api_client.post(url, document_json)
        assert response.status_code == BAD_REQUEST

    @pytest.mark.parametrize(
        argnames='user, document',
        argvalues=(
            # check all cases by attorney
            ('attorney', 'private_attorney_document'),
            ('attorney', 'matter_document'),
            ('attorney', 'shared_document'),
            ('attorney', 'attorney_template_document'),

            # check all cases by shared attorney
            ('shared_attorney', 'private_shared_attorney_document'),
            ('shared_attorney', 'matter_document'),
            ('shared_attorney', 'shared_document'),
            ('shared_attorney', 'shared_attorney_template_document'),

            # check all cases by support
            ('support', 'private_support_document'),
            ('support', 'matter_document'),
            ('support', 'shared_document'),
            ('support', 'support_template_document'),
        ),
        indirect=True
    )
    def test_document_creation_with_different_parent(
        self, api_client: APIClient, document: models.Document,
        user: user_models.AppUser
    ):
        """Check logic behind api document creation process.

        Test creation in another folder.

        """
        if document.matter:
            document.matter.status = Matter.STATUS_OPEN
            document.matter.save()
        document_json = serialize_document(document)
        url = get_list_url()

        document_json['parent'] = factories.FolderFactory(owner=user).pk
        api_client.force_authenticate(user=user)
        response = api_client.post(url, document_json)

        assert response.status_code == CREATED
        response_data = json.loads(response.content)
        # Check that new folder appeared in db
        models.Document.objects.get(pk=response_data['id'])

    @pytest.mark.parametrize(
        argnames='user, document',
        argvalues=(
            # check all cases by attorney
            ('attorney', 'private_attorney_document'),
            ('attorney', 'matter_document'),
            ('attorney', 'shared_document'),
            ('attorney', 'attorney_template_document'),

            # check all cases by shared attorney
            ('shared_attorney', 'private_shared_attorney_document'),
            ('shared_attorney', 'matter_document'),
            ('shared_attorney', 'shared_document'),
            ('shared_attorney', 'shared_attorney_template_document'),

            # check all cases by support
            ('support', 'private_support_document'),
            ('support', 'matter_document'),
            ('support', 'shared_document'),
            ('support', 'support_template_document'),
        ),
        indirect=True
    )
    def test_document_editing(
        self, api_client: APIClient, document: models.Document,
        user: user_models.AppUser
    ):
        """Check logic behind api document editing."""
        if document.matter:
            document.matter.status = Matter.STATUS_OPEN
            document.matter.save()
        document_json = serialize_document(document)
        url = get_detail_url(document)
        document_json['title'] = f"{document_json['title']}(1)"
        api_client.force_authenticate(user=user)
        response = api_client.put(url, document_json)

        assert response.status_code == OK
        response_data = json.loads(response.content)
        updated_model = models.Document.objects.get(pk=response_data['id'])
        # Check that document was updated
        assert updated_model.title == document_json['title']

    @pytest.mark.parametrize(
        argnames='user, document',
        argvalues=(
            # check all cases by attorney
            ('attorney', 'private_attorney_document'),
            ('attorney', 'matter_document'),
            ('attorney', 'shared_document'),
            ('attorney', 'attorney_template_document'),

            # check all cases by shared attorney
            ('shared_attorney', 'private_shared_attorney_document'),
            ('shared_attorney', 'matter_document'),
            ('shared_attorney', 'shared_document'),
            ('shared_attorney', 'shared_attorney_template_document'),

            # check all cases by support
            ('support', 'private_support_document'),
            ('support', 'matter_document'),
            ('support', 'shared_document'),
            ('support', 'support_template_document'),
        ),
        indirect=True
    )
    def test_document_deletion(
        self, api_client: APIClient, document: models.Document,
        user: user_models.AppUser, mocker
    ):
        """Check logic behind api document deletion process for users."""
        if document.matter:
            document.matter.status = Matter.STATUS_OPEN
            document.matter.save()

        delete = mocker.patch('apps.documents.models.Document.delete')
        url = get_detail_url(document)
        api_client.force_authenticate(user=user)
        response = api_client.delete(url)
        assert response.status_code == NO_CONTENT
        delete.assert_called()
