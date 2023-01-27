import pytest

from ...promotion.factories import EventFactory
from ...users.models import AppUser, Client
from .. import models
from .conftest import NOTIFICATION_TYPES_DATA


@pytest.fixture(scope='session')
def notification_dispatch_and_setting(
    django_db_blocker, client: Client
):
    """Create dispatch and setting for testing."""
    with django_db_blocker.unblock():
        event = EventFactory(attorney=client.user.followed_attorneys.first())
        notification_type = models.NotificationType.objects.get(
            runtime_tag='new_attorney_event'
        )
        notification = models.Notification.objects.create(
            title='Test',
            type=notification_type,
            content_object=event
        )
        dispatch = models.NotificationDispatch.objects.create(
            notification=notification, recipient=client.user
        )
        setting, _ = models.NotificationSetting.objects.get_or_create(
            user=client.user,
            notification_type=notification_type,
        )
        return dispatch, setting


class TestNotificationTypeQuerySet:
    """Test NotificationTypeQuerySet methods."""

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney',
            'support',
        ),
        indirect=True
    )
    def test_user_types_queryset_for_client(self, user: AppUser):
        """Test user types filter for all user types.

        Method user_types must return for user all notification types
        available for user's user type.

        """
        types_from_db = models.NotificationType.objects.user_types(
            user=user
        )

        assert types_from_db.count()
        client_types = [
            notification_type
            for notification_type in NOTIFICATION_TYPES_DATA
            if notification_type[f'is_for_{user.user_type}']
        ]
        assert types_from_db.count() == len(client_types)


class TestNotificationNotificationDispatchQuerySet:
    """Test NotificationNotificationDispatchQuerySe methods."""

    def test_allowed_to_notify(self, notification_dispatch_and_setting):
        """Check that filter returns dispatches with notifications turn on.

        Notification is turn on, when notification setting for notification's
        type has by_email and by_push equal to True.

        """
        dispatch, setting = notification_dispatch_and_setting
        setting.by_push = True
        setting.by_email = True
        setting.save()
        dispatches = models.NotificationDispatch.objects. \
            get_allowed_to_notify()

        assert dispatches.count()
        assert dispatch in dispatches

    def test_allowed_to_notify_no_dispatches(
        self,
        notification_dispatch_and_setting
    ):
        """Test case when notifications are turn off."""
        dispatch, setting = notification_dispatch_and_setting
        setting.by_push = False
        setting.by_email = False
        setting.save()
        dispatches = models.NotificationDispatch.objects. \
            get_allowed_to_notify()

        assert dispatch not in dispatches
