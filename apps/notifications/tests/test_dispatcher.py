from unittest.mock import MagicMock, patch

import pytest

from ...users.models import Attorney, UserStatistic
from ..models import Notification, NotificationSetting
from ..services.dispatcher import NotificationDispatcher
from ..services.resources import (
    BaseNotificationResource,
    OpportunitiesNotificationResource,
)


@pytest.fixture(scope='module')
def stat(django_db_blocker, attorney: Attorney) -> UserStatistic:
    """Create user statistic for testing."""
    with django_db_blocker.unblock():
        return UserStatistic.objects.create(
            user=attorney.user,
            tag=UserStatistic.TAG_OPPORTUNITIES,
        )


@pytest.fixture(scope='module')
def resource(
    django_db_blocker, stat: UserStatistic
) -> OpportunitiesNotificationResource:
    """Create resource for testing."""
    with django_db_blocker.unblock():
        return OpportunitiesNotificationResource(instance=stat)


@pytest.fixture(scope='module')
def notification(
    django_db_blocker, resource: BaseNotificationResource
) -> Notification:
    """Create notification for testing."""
    with django_db_blocker.unblock():
        return Notification.objects.create(
            type=resource.notification_type,
            title=resource.title,
            content_object=resource.instance
        )


@pytest.fixture(scope='module')
def dispatcher(
    resource: BaseNotificationResource, notification: Notification
) -> NotificationDispatcher:
    """Create notification dispatcher for testing."""
    return NotificationDispatcher(
        resource=resource,
        notification=notification,
    )


@pytest.fixture(scope='module')
def notification_setting(
    django_db_blocker, attorney: Attorney, resource: BaseNotificationResource
) -> NotificationSetting:
    """Create notification settings for testing."""
    with django_db_blocker.unblock():
        setting, _ = NotificationSetting.objects.get_or_create(
            user=attorney.user,
            notification_type=resource.notification_type
        )
        return setting


class TestDispatcher:
    """Tests for `NotificationDispatcher` class."""

    def test_notification_dispatch_generation(
        self,
        attorney: Attorney,
        dispatcher: NotificationDispatcher,
        notification_setting: NotificationSetting,
    ):
        """Test notification_dispatch generation."""
        notification_setting.by_email = True
        notification_setting.by_push = True
        notification_setting.save()

        dispatches = dispatcher.get_notification_dispatches_queryset()

        assert dispatches.filter(recipient=attorney.user).exists()

    def test_notification_dispatch_generation_with_turn_off_settings(
        self,
        attorney: Attorney,
        dispatcher: NotificationDispatcher,
        notification_setting: NotificationSetting,
    ):
        """Test notification_dispatch generation when settings are turn off."""
        notification_setting.by_email = False
        notification_setting.by_push = False
        notification_setting.save()

        dispatches = dispatcher.get_notification_dispatches_queryset()

        assert not dispatches.filter(recipient=attorney.user).exists()

    def test_notification_dispatch_generation_with_one_turn_off_setting(
        self,
        attorney: Attorney,
        dispatcher: NotificationDispatcher,
        notification_setting: NotificationSetting,
    ):
        """Test dispatch generation when one setting is turn off."""
        notification_setting.by_email = False
        notification_setting.by_push = True
        notification_setting.save()

        dispatches = dispatcher.get_notification_dispatches_queryset()

        assert dispatches.filter(recipient=attorney.user).exists()

    @patch('apps.notifications.services.dispatcher.send_notification_by_email')
    @patch('apps.notifications.services.dispatcher.send_notification_by_push')
    def test_notification_dispatching(
        self,
        send_by_push_mock: MagicMock,
        send_by_email_mock: MagicMock,
        dispatcher: NotificationDispatcher,
        notification_setting: NotificationSetting,
    ):
        """Test dispatching with all settings turn on."""
        notification_setting.by_email = True
        notification_setting.by_push = True
        notification_setting.save()

        dispatcher.notify()

        send_by_push_mock.assert_called()
        send_by_email_mock.assert_called()

    @patch('apps.notifications.services.dispatcher.send_notification_by_email')
    @patch('apps.notifications.services.dispatcher.send_notification_by_push')
    def test_notification_dispatching_with_email_turn_off(
        self,
        send_by_push_mock: MagicMock,
        send_by_email_mock: MagicMock,
        dispatcher: NotificationDispatcher,
        notification_setting: NotificationSetting,
    ):
        """Test dispatching with email turned off."""
        notification_setting.by_email = False
        notification_setting.by_push = True
        notification_setting.save()

        dispatcher.notify()

        send_by_push_mock.assert_called()
        send_by_email_mock.assert_not_called()

    @patch('apps.notifications.services.dispatcher.send_notification_by_email')
    @patch('apps.notifications.services.dispatcher.send_notification_by_push')
    def test_notification_dispatching_with_push_turn_off(
        self,
        send_by_push_mock: MagicMock,
        send_by_email_mock: MagicMock,
        dispatcher: NotificationDispatcher,
        notification_setting: NotificationSetting,
    ):
        """Test dispatching with push turned off."""
        notification_setting.by_email = True
        notification_setting.by_push = False
        notification_setting.save()

        dispatcher.notify()

        send_by_push_mock.assert_not_called()
        send_by_email_mock.assert_called_once()
