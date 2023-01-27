from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import BAD_REQUEST, CREATED, NOT_FOUND

from apps.business.models import Matter

from ....users.models import AppUser
from ... import factories, models
from ...api import serializers


def get_duplicate_document_url(document: models.Document):
    """Get url for document duplicating."""
    return reverse_lazy('v1:documents-duplicate', kwargs={'pk': document.pk})


class TestClientAPI:
    """Test duplicate feature for client."""

    @pytest.mark.parametrize(
        argnames='document, status_code',
        argvalues=(
            ('private_attorney_document', NOT_FOUND),
            ('private_shared_attorney_document', NOT_FOUND),
            ('private_support_document', NOT_FOUND),
            ('matter_document', NOT_FOUND),
            ('other_matter_document', NOT_FOUND),
            ('shared_document', CREATED),
            ('other_shared_document', NOT_FOUND),
            ('admin_template_document', NOT_FOUND),
            ('attorney_template_document', NOT_FOUND),
            ('shared_attorney_template_document', NOT_FOUND),
            ('support_template_document', NOT_FOUND),
        ),
        indirect=True
    )
    def test_document_duplicate_access_restriction(
        self, auth_client_api: APIClient, document: models.Document,
        status_code: int
    ):
        """Client can't duplicate matter, attorney and templates documents."""
        document_json = serializers.DocumentSerializer(instance=document).data
        document_json['title'] = f"{document_json['title']}(1)"
        url = get_duplicate_document_url(document)
        response = auth_client_api.post(url, document_json)
        assert response.status_code == status_code, response.data

    def test_document_duplicate_unique_restriction(
        self, auth_client_api: APIClient, shared_document: models.Document
    ):
        """We can't create duplicate without changing title or parent."""
        document_json = serializers.DocumentSerializer(
            instance=shared_document
        ).data
        url = get_duplicate_document_url(shared_document)
        response = auth_client_api.post(url, document_json)
        assert response.status_code == BAD_REQUEST

        # Test the same, but all params are None
        response = auth_client_api.post(
            url, {'title': None, 'parent': None}, format='json'
        )
        assert response.status_code == BAD_REQUEST

    def test_document_duplicate_with_parent(
        self, auth_client_api: APIClient, shared_document: models.Document
    ):
        """Test duplication on document with different parent.

        Client can't copy file from shared folder to another folder.
        Client can only copy shared documents.

        """
        document_json = serializers.DocumentSerializer(
            instance=shared_document
        ).data
        url = get_duplicate_document_url(shared_document)
        new_folder = factories.FolderFactory(
            owner=shared_document.owner,
            matter=shared_document.matter,
            parent=shared_document.parent
        )
        document_json['parent'] = new_folder.pk
        response = auth_client_api.post(url, document_json)
        assert response.status_code == BAD_REQUEST, response.data


class TestAttorneySupportAPI:
    """Test duplicate feature for attorney and support."""

    @pytest.mark.parametrize(
        argnames='user, document',
        argvalues=(
            # check all documents by attorney
            ('attorney', 'private_attorney_document'),
            ('attorney', 'matter_document'),
            ('attorney', 'shared_document'),
            ('attorney', 'attorney_template_document'),

            # check all documents by shared attorney
            ('shared_attorney', 'private_shared_attorney_document'),
            ('shared_attorney', 'matter_document'),
            ('shared_attorney', 'shared_document'),
            ('shared_attorney', 'shared_attorney_template_document'),

            # check all documents by support
            ('support', 'private_support_document'),
            ('support', 'matter_document'),
            ('support', 'shared_document'),
            ('support', 'support_template_document'),
        ),
        indirect=True
    )
    def test_document_duplicate_unique_restriction(
        self, api_client: APIClient, user: AppUser, document: models.Document
    ):
        """We can't create duplicate without changing title or parent."""
        if document.matter:
            document.matter.status = Matter.STATUS_OPEN
            document.matter.save()

        document_json = serializers.DocumentSerializer(instance=document).data
        url = get_duplicate_document_url(document)
        api_client.force_authenticate(user=user)
        response = api_client.post(url, document_json)
        assert response.status_code == BAD_REQUEST

        # Test the same, but all params are None
        response = api_client.post(
            url, {'title': None, 'parent': None}, format='json'
        )
        assert response.status_code == BAD_REQUEST

    @pytest.mark.parametrize(
        argnames='user, document',
        argvalues=(
            # check all documents by attorney
            ('attorney', 'private_attorney_document'),
            ('attorney', 'matter_document'),
            ('attorney', 'shared_document'),
            ('attorney', 'attorney_template_document'),

            # check all documents by shared attorney
            ('shared_attorney', 'private_shared_attorney_document'),
            ('shared_attorney', 'matter_document'),
            ('shared_attorney', 'shared_document'),
            ('shared_attorney', 'shared_attorney_template_document'),

            # check all documents by support
            ('support', 'private_support_document'),
            ('support', 'matter_document'),
            ('support', 'shared_document'),
            ('support', 'support_template_document'),
        ),
        indirect=True
    )
    def test_document_duplicate_with_title(
        self, api_client: APIClient, user: AppUser, document: models.Document
    ):
        """Test duplication on document with different title."""
        if document.matter:
            document.matter.status = Matter.STATUS_OPEN
            document.matter.save()

        document_json = serializers.DocumentSerializer(instance=document).data
        url = get_duplicate_document_url(document)
        document_json['title'] = f'{document.title}(1)'
        api_client.force_authenticate(user=user)
        response = api_client.post(url, document_json)
        assert response.status_code == CREATED, response.data

        # Check that data of duplicated document in db
        duplicate = models.Document.objects.get(pk=response.data['id'])
        assert duplicate.title == f'{document.title}(1)'
        assert duplicate.parent_id == document.parent_id
        assert duplicate.matter_id == document.matter_id

    @pytest.mark.parametrize(
        argnames='user, document',
        argvalues=(
            # check all documents by attorney
            ('attorney', 'private_attorney_document'),
            ('attorney', 'matter_document'),
            ('attorney', 'shared_document'),
            ('attorney', 'attorney_template_document'),

            # check all documents by shared attorney
            ('shared_attorney', 'private_shared_attorney_document'),
            ('shared_attorney', 'matter_document'),
            ('shared_attorney', 'shared_document'),
            ('shared_attorney', 'shared_attorney_template_document'),

            # check all documents by support
            ('support', 'private_support_document'),
            ('support', 'matter_document'),
            ('support', 'shared_document'),
            ('support', 'support_template_document'),
        ),
        indirect=True
    )
    def test_document_duplicate_with_parent(
        self, api_client: APIClient, user: AppUser, document: models.Document
    ):
        """Test duplication on document with different parent."""
        if document.matter:
            document.matter.status = Matter.STATUS_OPEN
            document.matter.save()

        document_json = serializers.DocumentSerializer(instance=document).data
        url = get_duplicate_document_url(document)

        new_folder = factories.FolderFactory(
            owner=document.owner,
            matter=document.matter,
            parent=document.parent
        )
        document_json['parent'] = new_folder.pk
        api_client.force_authenticate(user=user)
        response = api_client.post(url, document_json)
        assert response.status_code == CREATED

        # Check that data of duplicated document in db
        duplicate = models.Document.objects.get(pk=response.data['id'])
        assert duplicate.title == document.title
        assert duplicate.parent_id == new_folder.pk
        assert duplicate.matter_id == document.matter_id
