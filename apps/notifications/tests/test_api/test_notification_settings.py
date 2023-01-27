from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from ....notifications import models
from ....users.models import AppUser


def get_list_url():
    """Get url for creating and editing notification setting."""
    return reverse_lazy('v1:notifications_settings-list')


class TestAuthUserAPI:
    """Test notification settings api for auth users."""

    @staticmethod
    def get_notification_type(user: AppUser) -> models.NotificationType:
        """Get notification type for user"""
        return models.NotificationType.objects.user_types(
            user=user
        ).first()

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney',
            'support',
        ),
        indirect=True
    )
    def test_create_user_setting(self, api_client: APIClient, user: AppUser):
        """Test that users can create notification setting."""
        notification_type = self.get_notification_type(user=user)

        setting_json = {
            'notification_type': notification_type.pk,
            'by_email': True,
            'by_push': True
        }
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.post(url, data=setting_json)
        assert response.status_code == status.HTTP_201_CREATED, \
            response.data

        # Check that settings are in db
        models.NotificationSetting.objects.get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney',
            'support',
        ),
        indirect=True
    )
    def test_update_user_setting(self, api_client: APIClient, user: AppUser):
        """Test that users can update notification setting."""
        notification_type = self.get_notification_type(user=user)

        setting_json = {
            'notification_type': notification_type.pk,
            'by_email': True,
            'by_push': False
        }
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.post(url, data=setting_json)
        assert response.status_code == status.HTTP_201_CREATED, \
            response.data

        # Check that settings are in db and they were updated
        setting = models.NotificationSetting.objects.get(
            pk=response.data['id']
        )
        assert not setting.by_push
        assert setting.by_email

    @pytest.mark.parametrize(
        argnames='user, other_user',
        argvalues=(
            ('client', 'attorney'),
            ('client', 'support'),
            ('attorney', 'client'),
            ('attorney', 'support'),
            ('support', 'attorney'),
            ('support', 'client'),
        ),
        indirect=True
    )
    def test_create_user_setting_incorrect_type(
        self,
        api_client: APIClient,
        user: AppUser,
        other_user: AppUser
    ):
        """Test that users can't create setting with incorrect type.

        Incorrect type for client is when recipient_type is not `all` or
        `client`.
        Incorrect type for attorney is when recipient_type is not `all` or
        `attorney`.

        """
        notification_type = models.NotificationType.objects.filter(
            **{f'is_for_{user.user_type}': False}
        ).first()

        setting_json = {
            'notification_type': notification_type.pk,
        }
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.post(url, data=setting_json)
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            response.data
