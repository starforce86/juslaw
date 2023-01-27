import logging
import uuid

from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from libs.docusign import constants

from ... import models


def get_save_consent_url() -> str:
    """Get url for `save-consent` docusign callback."""
    return reverse_lazy('v1:callbacks-save-consent')


def get_update_envelope_status() -> str:
    """Get url for `update-envelope-status` docusign callback."""
    return reverse_lazy('v1:callbacks-update-envelope-status')


class TestESignCallbacksAPI:
    """Class to test `ESignCallbacksView`."""

    def test_save_consent_no_impersonated(self, api_client: APIClient):
        """Test `save_consent` api callback when no impersonated user exists.
        """
        data = {'code': 'fake code', 'state': str(uuid.uuid4())}
        response = api_client.get(get_save_consent_url(), data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data is None

    @pytest.mark.parametrize(
        'error_key', ['error', 'error_message']
    )
    def test_save_consent_error_consent(
        self, error_key: str, api_client: APIClient,
        esign_profile: models.ESignProfile, caplog
    ):
        """Test `save_consent` api callback when consent data contains errors.
        """
        data = {
            'code': 'fake code',
            'state': esign_profile.consent_id,
            error_key: 'some error'
        }
        with caplog.at_level(logging.DEBUG, logger='docusign'):
            response = api_client.get(get_save_consent_url(), data=data)
            assert response.status_code == status.HTTP_302_FOUND
            # check that debug logger info was added
            assert len(caplog.records) == 1

    def test_save_consent(
        self, api_client: APIClient, esign_profile: models.ESignProfile,
        caplog, mocker
    ):
        """Test `save_consent` api callback when consent data is valid."""
        mocker.patch('apps.esign.adapters.DocuSignAdapter.save_consent')
        data = {'code': 'fake code', 'state': esign_profile.consent_id}
        with caplog.at_level(logging.DEBUG, 'docusign'):
            response = api_client.get(get_save_consent_url(), data=data)
            assert response.status_code == status.HTTP_302_FOUND
            # check that no logging errors appeared after test run
            assert len(caplog.records) == 0

    def test_update_envelope_status_not_existing_envelope(
        self, api_client: APIClient, caplog
    ):
        """Test `update_envelope_status` with not existing envelope."""
        # clean logs queue to check that new error appeared in this test
        caplog.clear()
        data = {
            'EnvelopeStatus': {
                'EnvelopeID': 'fake docusign id',
                'Status': constants.ENVELOPE_STATUS_DELIVERED
            }
        }
        with caplog.at_level(logging.WARNING, logger='docusign'):
            response = api_client.post(
                get_update_envelope_status(), data=data
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            # check that new logging error appeared after test run
            assert len(caplog.records) == 1

    def test_update_envelope_status(
        self, api_client: APIClient, envelope: models.Envelope, caplog
    ):
        """Test `update_envelope_status` with existing envelope."""
        # clean logs queue to check that no new error appeared in this test
        caplog.clear()
        assert envelope.status != constants.ENVELOPE_STATUS_DELIVERED

        data = {
            'EnvelopeStatus': {
                'EnvelopeID': envelope.docusign_id,
                'Status': constants.ENVELOPE_STATUS_DELIVERED.capitalize()
            }
        }
        response = api_client.post(
            get_update_envelope_status(), data=data
        )
        envelope.refresh_from_db()
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert envelope.status == constants.ENVELOPE_STATUS_DELIVERED
        # check that no logging errors appeared after test run
        assert len(caplog.records) == 0
