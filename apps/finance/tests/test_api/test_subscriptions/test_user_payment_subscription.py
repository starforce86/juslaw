import uuid
from unittest.mock import MagicMock

from django.urls import reverse_lazy

from rest_framework.test import APIClient

from libs.testing.constants import OK


def get_url():
    """Get url for `getting setup intent`."""
    return reverse_lazy('v1:subscribe-get-setup-intent')


def test_get_setup_intent(api_client: APIClient, mocker):
    """Test `get_setup_intent` API method."""
    expected_secret = str(uuid.uuid4())
    mocker.patch(
        'djstripe.models.SetupIntent._api_create',
        return_value=MagicMock(client_secret=expected_secret)
    )

    url = get_url()
    response = api_client.get(url)

    assert response.status_code == OK
    assert response.data['client_secret'] == expected_secret
