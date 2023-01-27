from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import BAD_REQUEST, CREATED, NOT_FOUND, OK

from ....users.models import AppUser
from ... import models
from ...api import serializers


def get_list_url():
    """Get url for video call creation and list retrieval."""
    return reverse_lazy('v1:video-calls-list')


def get_detail_url(video_call: models.VideoCall):
    """Get url for video call retrieval."""
    return reverse_lazy(
        'v1:video-calls-detail', kwargs={'pk': video_call.pk}
    )


@pytest.fixture
def call(
    request,
    attorney_video_call: models.VideoCall,
    shared_attorney_video_call: models.VideoCall,
    support_video_call: models.VideoCall,
    other_video_call: models.VideoCall,
) -> models.VideoCall:
    """Fixture to parametrize video_call fixtures."""
    mapping = {
        'attorney_video_call': attorney_video_call,
        'shared_attorney_video_call': shared_attorney_video_call,
        'support_video_call': support_video_call,
        'other_video_call': other_video_call,
    }
    return mapping.get(request.param)


class TestAuthUserAPI:
    """Test video call api for auth users.

    Clients and attorney can make video calls.

    """

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney',
            # shared attorney and support
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_get_list_video_call(
        self, api_client: APIClient, user: AppUser,
        attorney_video_call: models.VideoCall,
        shared_attorney_video_call: models.VideoCall,
        support_video_call: models.VideoCall
    ):
        """Test that users can get details of only it's calls."""
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == OK

        video_calls = models.VideoCall.objects.available_for_user(
            user=user
        )
        print(video_calls)
        assert video_calls.count() == response.data['count']
        for video_call_data in response.data['results']:
            video_calls.get(pk=video_call_data['id'])

    @pytest.mark.parametrize(
        argnames='user, call, status_code',
        argvalues=(
            ('client', 'attorney_video_call', OK),
            # shared attorney and support
            ('client', 'shared_attorney_video_call', OK),
            ('client', 'support_video_call', OK),

            ('attorney', 'attorney_video_call', OK),
            # shared attorney and support
            ('attorney', 'shared_attorney_video_call', NOT_FOUND),
            ('attorney', 'support_video_call', NOT_FOUND),

            ('shared_attorney', 'attorney_video_call', NOT_FOUND),
            # shared attorney and support
            ('shared_attorney', 'shared_attorney_video_call', OK),
            ('shared_attorney', 'support_video_call', NOT_FOUND),

            ('support', 'attorney_video_call', NOT_FOUND),
            # shared attorney and support
            ('support', 'shared_attorney_video_call', NOT_FOUND),
            ('support', 'support_video_call', OK),
        ),
        indirect=True
    )
    def test_retrieve_video_call(
        self,  api_client: APIClient, user: AppUser, call: models.VideoCall,
        status_code: int
    ):
        """Test that users can only get details of it's video calls"""
        url = get_detail_url(call)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == status_code

        if response.status_code == OK:
            models.VideoCall.objects.available_for_user(
                user=user
            ).get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user, call, status_code',
        argvalues=(
            ('attorney', 'attorney_video_call', CREATED),
            ('client', 'attorney_video_call', CREATED),

            ('shared_attorney', 'shared_attorney_video_call', CREATED),
            ('client', 'shared_attorney_video_call', CREATED),

            ('support', 'support_video_call', CREATED),
            ('client', 'support_video_call', CREATED),

            ('attorney', 'other_video_call', BAD_REQUEST),
            ('client', 'other_video_call', BAD_REQUEST),
            ('shared_attorney', 'other_video_call', BAD_REQUEST),
            ('support', 'other_video_call', BAD_REQUEST),
        ),
        indirect=True
    )
    def test_create_video_call(
        self,
        api_client: APIClient,
        user: AppUser,
        call: models.VideoCall,
        status_code: int
    ):
        """Test that creation of Video call works correctly."""
        video_call_json = serializers.VideoCallSerializer(
            instance=call
        ).data
        video_call_json['participants'] = call.participants.exclude(
            pk=user.pk
        ).values_list('pk', flat=True)

        api_client.force_authenticate(user=user)
        url = get_list_url()
        response = api_client.post(url, video_call_json)

        assert response.status_code == status_code

        # Check that new Video call appeared in db
        if response.status_code == CREATED:
            models.VideoCall.objects.get(pk=response.data['id'])
