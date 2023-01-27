import json

from django.urls import reverse_lazy
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from ...promotion import factories, models
from ...users.models import Attorney
from ..api import serializers


def get_list_url() -> str:
    """Get url for events creation and retrieval."""
    return reverse_lazy('v1:events-list')


def get_detail_url(event: models.Event) -> str:
    """Get url for events editing and deletion."""
    return reverse_lazy('v1:events-detail', kwargs={'pk': event.pk})


@pytest.fixture(scope='module')
def event(django_db_blocker, attorney) -> models.Event:
    """Create event for testing."""
    with django_db_blocker.unblock():
        return factories.EventFactory(start=timezone.now(), attorney=attorney)


@pytest.fixture(scope='module')
def other_event(django_db_blocker) -> models.Event:
    """Create other event for testing."""
    with django_db_blocker.unblock():
        return factories.EventFactory(start=timezone.now())


class TestNonAuthUserAPI:
    """Test promotion api for non authenticated users.

    Non authenticated users can only retrieve events.

    """

    def test_events_retrieval(self, api_client: APIClient):
        """Check that anon users can get list of events."""
        url = get_list_url()

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_event_retrieval(
        self, api_client: APIClient, event: models.Event
    ):
        """Check that anon users can get details of one event."""
        url = get_detail_url(event)

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_event_creation(
        self, api_client: APIClient, event: models.Event,
    ):
        """Check that non-authenticated users can't create events."""
        event_json = serializers.EventSerializer(instance=event).data
        url = get_list_url()

        response = api_client.post(url, event_json)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestClientAPI:
    """Test promotion api for client.

    Client can only retrieve events.

    """

    def test_event_creation(
        self, auth_client_api: APIClient, event: models.Event,
    ):
        """Check that clients can't create events."""
        event_json = serializers.EventSerializer(instance=event).data
        url = get_list_url()

        response = auth_client_api.post(url, event_json)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_events_retrieval(
        self, auth_client_api: APIClient
    ):
        """Check that clients can get list of events."""
        url = get_list_url()

        response = auth_client_api.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_event_retrieval(
        self, auth_client_api: APIClient, event: models.Event,
    ):
        """Check that clients can get details of one event."""
        url = get_detail_url(event)

        response = auth_client_api.get(url)
        assert response.status_code == status.HTTP_200_OK


class TestAttorneyAPI:
    """Test promotion api for attorney.

    Attorney can retrieve and create events, also update and delete it's own
    events.

    """

    def test_events_retrieval(
        self, auth_attorney_api: APIClient
    ):
        """Check that attorney can get list of events."""
        url = get_list_url()

        response = auth_attorney_api.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_event_retrieval(
        self, auth_attorney_api: APIClient, event: models.Event,
    ):
        """Check that attorney can get details of one event."""
        url = get_detail_url(event)

        response = auth_attorney_api.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_event_creation(
        self, auth_attorney_api: APIClient, event: models.Event,
    ):
        """Check that attorney can create event."""
        event_json = serializers.EventSerializer(instance=event).data
        url = get_list_url()

        response = auth_attorney_api.post(url, event_json)
        assert response.status_code == status.HTTP_201_CREATED

        response_data = json.loads(response.content)
        # Check that new event appeared in db
        models.Event.objects.get(pk=response_data['id'])

    def test_event_editing(
        self, auth_attorney_api: APIClient, event: models.Event,
    ):
        """Check that attorney can get edit event."""
        event_json = serializers.EventSerializer(instance=event).data
        event_json['title'] = 'Test'
        event_json['is_all_day'] = True
        url = get_detail_url(event)

        response = auth_attorney_api.put(url, event_json)
        assert response.status_code == status.HTTP_200_OK

        response_data = json.loads(response.content)
        # Check updated fields
        updated_event = models.Event.objects.get(pk=response_data['id'])
        assert updated_event.title == 'Test'
        assert updated_event.is_all_day

    def test_event_edit_foreign_event(
        self, auth_attorney_api: APIClient, other_event: models.Event,
    ):
        """Check that attorney can't get edit foreign event."""
        url = get_detail_url(other_event)

        response = auth_attorney_api.put(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_event_deletion(
        self, auth_attorney_api: APIClient, attorney: Attorney
    ):
        """Check that attorney can delete it's own event."""
        event = factories.EventFactory(attorney=attorney)
        url = get_detail_url(event)

        response = auth_attorney_api.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Check that event was deleted in db
        with pytest.raises(models.Event.DoesNotExist):
            models.Event.objects.get(pk=event.id)

    def test_event_delete_foreign_event(
        self, auth_attorney_api: APIClient, other_event: models.Event
    ):
        """Check that attorney can't delete foreign event."""
        url = get_detail_url(other_event)

        response = auth_attorney_api.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
