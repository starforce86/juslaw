from unittest.mock import MagicMock

from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from ....users.models import AppUser, Attorney
from ... import models


def get_list_url() -> str:
    """Get url for retrieving envelopes."""
    return reverse_lazy('v1:envelope-list')


def get_detail_url(envelope: models.Envelope) -> str:
    """Get url for retrieving envelope."""
    return reverse_lazy(
        'v1:envelope-detail', kwargs={'pk': envelope.pk}
    )


class TestEnvelopeAPI:
    """Class to test `EnvelopeViewSet`."""

    @pytest.mark.parametrize(
        'user,status_code', [
            (None, status.HTTP_401_UNAUTHORIZED),
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_200_OK),
        ], indirect=True
    )
    def test_get_envelopes_list(
        self, api_client: APIClient, user: AppUser, status_code: int
    ):
        """Test `list` envelopes.

        Only authenticated attorneys can get envelopes list.

        """
        api_client.force_authenticate(user=user)
        response = api_client.get(get_list_url())
        # no 400 exception should be raised for `list` method when `return_url`
        # is not set
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        'user,status_code', [
            (None, status.HTTP_401_UNAUTHORIZED),
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_400_BAD_REQUEST),
        ], indirect=True
    )
    def test_retrieve_envelope_no_return_url(
        self, api_client: APIClient, user: AppUser, envelope: models.Envelope,
        status_code: int
    ):
        """Test `retrieve` envelope.

        Only authenticated attorneys can get envelope details, also it is not
        allowed to get envelope without required `return_url`.

        """
        api_client.force_authenticate(user=user)
        response = api_client.get(get_detail_url(envelope))
        # 400 exception should be raised for `retrieve` method when
        # `return_url` is not set for authorized attorneys.
        assert response.status_code == status_code

    def test_retrieve_envelope_with_return_url(
        self, auth_attorney_api: APIClient, attorney: Attorney,
        envelope: models.Envelope, mocker
    ):
        """Test `retrieve` envelope.

        Only authenticated attorneys can get envelope details, also it is not
        allowed to get envelope without required `return_url`.

        """
        get_envelope_edit_link_mock = mocker.patch(
            'libs.docusign.clients.DocuSignClient.get_envelope_edit_link',
        )
        get_envelope_edit_link_mock.return_value = None
        url = get_detail_url(envelope)
        response = auth_attorney_api.get(
            f'{url}?return_url=http://example.com'
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize(
        'user,status_code', [
            (None, status.HTTP_401_UNAUTHORIZED),
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_400_BAD_REQUEST),
        ], indirect=True
    )
    def test_create_envelope_no_return_url(
        self, api_client: APIClient, user: AppUser, envelope: models.Envelope,
        status_code: int
    ):
        """Test `create` envelope.

        Only authenticated attorneys can create envelopes, also it is not
        allowed to make it without required `return_url`.

        """
        api_client.force_authenticate(user=user)
        response = api_client.post(get_list_url())
        # 400 exception should be raised for `create` method when
        # `return_url` is not set for authorized attorneys.
        assert response.status_code == status_code

    def test_create_envelope_with_return_url(
        self, auth_attorney_api: APIClient, attorney: Attorney,
        matter: models.Matter, mocker
    ):
        """Test `create` envelope.

        Only authenticated attorneys can create envelopes, also it is not
        allowed to make it without required `return_url`.

        """
        get_envelope_edit_link_mock = mocker.patch(
            'libs.docusign.clients.DocuSignClient.get_envelope_edit_link',
        )
        get_envelope_edit_link_mock.return_value = None
        get_envelope_edit_link_mock = mocker.patch(
            'libs.docusign.clients.DocuSignClient.create_envelope',
        )
        get_envelope_edit_link_mock.return_value = MagicMock(
            envelope_id='fake envelope_id'
        )
        url = get_list_url()
        data = {
            'matter': matter.id,
            'documents': [
                {'file': f'http://localhost{attorney.user.avatar.path}'}
            ],
            'type': models.Envelope.TYPE_EXTRA
        }
        response = auth_attorney_api.post(
            f'{url}?return_url=http://example.com',
            data=data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        # check that new envelope was created with corresponding params
        envelope = models.Envelope.objects.filter(
            id=response.data['id']
        ).first()
        assert envelope
        assert envelope.matter == matter
        assert envelope.type == models.Envelope.TYPE_EXTRA
        assert envelope.documents.count() == 1
        assert envelope.docusign_id == 'fake envelope_id'
