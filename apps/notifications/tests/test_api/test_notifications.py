from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from ....notifications import factories, models
from ....promotion.factories import EventFactory
from ....users.models import AppUser, Attorney, Client, UserStatistic


def get_list_url() -> str:
    """Get url for retrieving notifications."""
    return reverse_lazy('v1:notifications-list')


def get_detail_url(notification_dispatch: models.NotificationDispatch) -> str:
    """Get url for retrieving notification."""
    return reverse_lazy(
        'v1:notifications-detail', kwargs={'pk': notification_dispatch.pk}
    )


def get_read_url(notification_dispatch: models.NotificationDispatch) -> str:
    """Get url for marking notification as `read`."""
    return reverse_lazy(
        'v1:notifications-read', kwargs={'pk': notification_dispatch.pk}
    )


def get_unread_url(notification_dispatch: models.NotificationDispatch) -> str:
    """Get url for marking notification as `unread`."""
    return reverse_lazy(
        'v1:notifications-unread', kwargs={'pk': notification_dispatch.pk}
    )


@pytest.fixture(scope='module', autouse=True)
def client_notification_dispatch(
    django_db_blocker,
    client: Client,
    attorney: Attorney,
) -> models.NotificationDispatch:
    """Create clients's notification dispatch for testing."""
    with django_db_blocker.unblock():
        notification_type = models.NotificationType.objects.get(
            runtime_tag='new_attorney_event'
        )
        content_object = EventFactory(attorney=attorney)
        return factories.NotificationDispatchFactory(
            recipient=client.user,
            notification__type=notification_type,
            notification__content_object=content_object,
            status=models.NotificationDispatch.STATUS_SENT
        )


@pytest.fixture(scope='module', autouse=True)
def attorney_notification_dispatch(
    django_db_blocker,
    attorney: Attorney,
) -> models.NotificationDispatch:
    """Create attorney's notification dispatch for testing."""
    with django_db_blocker.unblock():
        notification_type = models.NotificationType.objects.get(
            runtime_tag='new_opportunities'
        )
        content_object = UserStatistic.objects.create(
            user=attorney.user,
            tag=UserStatistic.TAG_OPPORTUNITIES,
        )
        return factories.NotificationDispatchFactory(
            recipient=attorney.user,
            notification__type=notification_type,
            notification__content_object=content_object,
            status=models.NotificationDispatch.STATUS_SENT
        )


@pytest.fixture
def notification_dispatch(
    request,
    client_notification_dispatch: models.NotificationDispatch,
    attorney_notification_dispatch: models.NotificationDispatch
) -> models.NotificationDispatch:
    """Fixture to use parametrize NotificationDispatch fixture."""
    mapping = {
        'client_notification_dispatch': client_notification_dispatch,
        'attorney_notification_dispatch': attorney_notification_dispatch,
    }
    notification_dispatch = mapping[request.param]
    return notification_dispatch


class TestAuthUserAPI:
    """Test notifications api for client."""

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney',
        ),
        indirect=True
    )
    def test_get_notification_list(self, api_client: APIClient, user: AppUser):
        """Test that users can get notifications."""
        url = get_list_url()
        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize(
        argnames='user, notification_dispatch',
        argvalues=(
            ('client', 'client_notification_dispatch'),
            ('attorney', 'attorney_notification_dispatch')
        ),
        indirect=True
    )
    def test_get_notification_detail(
        self,
        api_client: APIClient,
        user: AppUser,
        notification_dispatch: models.NotificationDispatch
    ):
        """Test that users can get notification details."""
        url = get_detail_url(notification_dispatch)
        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize(
        argnames='user, notification_dispatch',
        argvalues=(
            ('client', 'client_notification_dispatch'),
            ('attorney', 'attorney_notification_dispatch')
        ),
        indirect=True
    )
    def test_read_notification(
        self,
        api_client: APIClient,
        user: AppUser,
        notification_dispatch: models.NotificationDispatch
    ):
        """Test that users can mark notification as 'read'."""
        notification_dispatch.status = models.NotificationDispatch.STATUS_SENT
        notification_dispatch.save()

        url = get_read_url(notification_dispatch)
        api_client.force_authenticate(user=user)
        response = api_client.post(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        notification_dispatch.refresh_from_db()
        status_read = models.NotificationDispatch.STATUS_READ
        assert notification_dispatch.status == status_read

    @pytest.mark.parametrize(
        argnames='user, notification_dispatch',
        argvalues=(
            ('client', 'client_notification_dispatch'),
            ('attorney', 'attorney_notification_dispatch')
        ),
        indirect=True
    )
    def test_unread_notification(
        self,
        api_client: APIClient,
        user: AppUser,
        notification_dispatch: models.NotificationDispatch
    ):
        """Test that client can mark notification as 'unread'."""
        notification_dispatch.status = models.NotificationDispatch.STATUS_READ
        notification_dispatch.save()

        url = get_unread_url(notification_dispatch)
        api_client.force_authenticate(user=user)
        response = api_client.post(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        notification_dispatch.refresh_from_db()
        status_sent = models.NotificationDispatch.STATUS_SENT
        assert notification_dispatch.status == status_sent
