from django.core.exceptions import ValidationError
from django.db import IntegrityError

import pytest

from ...users.models import Attorney, Client
from .. import models


class TestNotificationSetting:
    """Test NotificationSetting model."""

    def test_notification_setting_with_wrong_type(
        self, attorney: Attorney, client: Client
    ):
        """Check that we can't create setting for type with wrong recipient.

        Recipient types:
            Client: all, client
            Attorney: all, attorney

        """

        client_notification_type = models.NotificationType.objects.filter(
            is_for_client=True,
            is_for_attorney=False,
        ).first()
        attorney_notification_type = models.NotificationType.objects.filter(
            is_for_client=False,
            is_for_attorney=True,
        ).first()

        with pytest.raises(ValidationError):
            wrong_attorney_setting = models.NotificationSetting(
                user=attorney.user, notification_type=client_notification_type
            )
            wrong_attorney_setting.clean()

        with pytest.raises(ValidationError):
            wrong_client_setting = models.NotificationSetting(
                user=client.user, notification_type=attorney_notification_type
            )
            wrong_client_setting.clean()

    def test_notification_setting_with_correct_type(
        self, attorney: Attorney, client: Client
    ):
        """Check that we can create setting for type with correct recipient."""
        client_notification_type = models.NotificationType.objects.filter(
            is_for_client=True,
            is_for_attorney=False,
        ).first()
        attorney_notification_type = models.NotificationType.objects.filter(
            is_for_client=False,
            is_for_attorney=True,
        ).first()
        common_notification_type = models.NotificationType.objects.filter(
            is_for_client=True,
            is_for_attorney=True,
        ).first()
        test_kwargs_tuple = (
            {
                'user': client.user,
                'notification_type': client_notification_type
            },
            {
                'user': attorney.user,
                'notification_type': attorney_notification_type
            },
            {
                'user': client.user,
                'notification_type': common_notification_type
            },
            {
                'user': attorney.user,
                'notification_type': common_notification_type
            },
        )
        for test_kwargs in test_kwargs_tuple:
            models.NotificationSetting(**test_kwargs).clean()

    def test_unique_setting_for_user_and_type(self, attorney: Attorney):
        """Test that notification settings for type must be unique for user.

        First we use get_or_create for notification setting(in case that some
        other test already created one. Then we try to create another one, and
        at that moment IntegrityError should be raises.

        """
        notification_type = models.NotificationType.objects.user_types(
            user=attorney.user
        ).first()
        models.NotificationSetting.objects.get_or_create(
            user=attorney.user, notification_type=notification_type
        )
        with pytest.raises(IntegrityError):
            models.NotificationSetting.objects.create(
                user=attorney.user, notification_type=notification_type
            )
