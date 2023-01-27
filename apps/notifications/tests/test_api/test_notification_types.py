from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from ....notifications import models
from ....users.models import AppUser


def get_list_url():
    """Get url for retrieving notification types."""
    return reverse_lazy('v1:notifications_types-list')


@pytest.mark.parametrize(
    argnames='user',
    argvalues=(
        'client',
        'attorney',
    ),
    indirect=True
)
def test_get_notification_types_for_auth_user(
    api_client: APIClient, user: AppUser
):
    """Check that user receives types for it's user type."""
    url = get_list_url()

    api_client.force_authenticate(user=user)
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    user_types = models.NotificationType.objects.user_types(
        user=user
    )

    assert response.data['count'] == user_types.count()
