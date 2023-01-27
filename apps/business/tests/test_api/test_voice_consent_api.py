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
)

from ....users.models import AppUser
from ... import models
from ...api import serializers
from ...factories import VoiceConsentFactory


def get_list_url():
    """Get url for voice-consent creation and list retrieval."""
    return reverse_lazy('v1:voice-consent-list')


def get_detail_url(voice_consent: models.VoiceConsent):
    """Get url for voice-consent editing and retrieval."""
    return reverse_lazy(
        'v1:voice-consent-detail', kwargs={'pk': voice_consent.pk}
    )


@pytest.fixture(scope='function')
def voice_consent_to_delete(matter: models.Matter) -> models.VoiceConsent:
    """Create test voice consent for deletion."""
    return VoiceConsentFactory(matter=matter)


@pytest.fixture
def voice_consent(
    request,
    client_voice_consent: models.VoiceConsent,
    voice_consent_to_delete: models.VoiceConsent,
    other_voice_consent: models.VoiceConsent,
) -> models.VoiceConsent:
    """Fixture to parametrize voice_consent fixtures."""
    mapping = {
        'client_voice_consent': client_voice_consent,
        'voice_consent_to_delete': voice_consent_to_delete,
        'other_voice_consent': other_voice_consent
    }
    voice_consent = mapping[request.param]
    return voice_consent


class TestAuthUserAPI:
    """Test voice consent api for auth users.

    Clients can only read and create new voice consents.
    Attorneys, shared attorneys and support can only read and delete voice
    consents available for them.

    """

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney',
            # shared attorney and support
            'support',
            'shared_attorney',
        ),
        indirect=True
    )
    def test_get_list_voice_consent(
        self,
        api_client: APIClient,
        user: AppUser,
        client_voice_consent: models.VoiceConsent
    ):
        """Test that users can get details of only it's voice consents."""
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == OK

        voice_consents = models.VoiceConsent.objects.available_for_user(
            user=user
        )
        assert voice_consents.count() == response.data['count']
        for voice_consent_data in response.data['results']:
            voice_consents.get(pk=voice_consent_data['id'])

    @pytest.mark.parametrize(
        argnames='user, voice_consent, status_code',
        argvalues=(
            ('client', 'client_voice_consent', OK),
            ('attorney', 'client_voice_consent', OK),
            # shared attorney and support
            ('support', 'client_voice_consent', OK),
            ('shared_attorney', 'client_voice_consent', OK),

            ('client', 'other_voice_consent', NOT_FOUND),
            ('attorney', 'other_voice_consent', NOT_FOUND),
            # shared attorney and support
            ('support', 'other_voice_consent', NOT_FOUND),
            ('shared_attorney', 'other_voice_consent', NOT_FOUND),
        ),
        indirect=True
    )
    def test_retrieve_voice_consent(
        self,
        api_client: APIClient,
        user: AppUser,
        voice_consent: models.VoiceConsent,
        status_code: int,
        matter: models.Matter
    ):
        """Test that users can only get details of it's voice consent."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        url = get_detail_url(voice_consent)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == status_code

        if response.status_code == OK:
            models.VoiceConsent.objects.available_for_user(
                user=user
            ).get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user, voice_consent, status_code',
        argvalues=(
            ('client', 'client_voice_consent', CREATED),
            ('attorney', 'client_voice_consent', FORBIDDEN),
            # shared attorney and support
            ('support', 'client_voice_consent', FORBIDDEN),
            ('shared_attorney', 'client_voice_consent', FORBIDDEN),
        ),
        indirect=True
    )
    def test_create_voice_consent(
        self,
        api_client: APIClient,
        user: AppUser,
        voice_consent: models.VoiceConsent,
        status_code: int
    ):
        """Test that client, but not attorney can create voice consent."""
        voice_consent_json = serializers.VoiceConsentSerializer(
            instance=voice_consent
        ).data
        voice_consent_json['file'] = (
            f'http://localhost{voice_consent.file.url}'
        )
        voice_consent_json['title'] = f'{voice_consent.title} (1)'
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.post(url, voice_consent_json)
        assert response.status_code == status_code

        # Check that new voice consent appeared in db
        if response.status_code == CREATED:
            models.VoiceConsent.objects.get(pk=response.data['id'])

    def test_create_duplicated_voice_consent(
        self,
        auth_client_api: APIClient,
        client_voice_consent: models.VoiceConsent,
    ):
        """Test that clients can't create duplicated voice consents."""
        voice_consent_json = serializers.VoiceConsentSerializer(
            instance=client_voice_consent
        ).data
        voice_consent_json['file'] = (
            f'http://localhost{client_voice_consent.file.url}'
        )
        url = get_list_url()

        response = auth_client_api.post(url, voice_consent_json)
        assert response.status_code == BAD_REQUEST

    @pytest.mark.parametrize(
        argnames='user, voice_consent, status_code',
        argvalues=(
            ('client', 'voice_consent_to_delete', FORBIDDEN),
            ('attorney', 'voice_consent_to_delete', NO_CONTENT),
            # shared attorney and support
            ('support', 'voice_consent_to_delete', NO_CONTENT),
            ('shared_attorney', 'voice_consent_to_delete', NO_CONTENT),

            ('client', 'other_voice_consent', FORBIDDEN),
            ('attorney', 'other_voice_consent', NOT_FOUND),
            # shared attorney and support
            ('support', 'other_voice_consent', NOT_FOUND),
            ('shared_attorney', 'other_voice_consent', NOT_FOUND),
        ),
        indirect=True
    )
    def test_delete_voice_consent(
        self,
        api_client: APIClient,
        user: AppUser,
        voice_consent: models.VoiceConsent,
        status_code: int
    ):
        """Test that client, but not attorney can delete own voice consent."""
        voice_consent.matter.status = models.Matter.STATUS_OPEN
        voice_consent.matter.save()

        url = get_detail_url(voice_consent)

        api_client.force_authenticate(user=user)
        response = api_client.delete(url)
        assert response.status_code == status_code
