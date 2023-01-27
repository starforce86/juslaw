import uuid
from unittest.mock import MagicMock

from django.conf import settings
from django.core.cache import cache
from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest
from intuitlib.exceptions import AuthClientError

from libs.quickbooks import default_quickbooks_client


def get_authorization_url():
    """Get url for `get_authorization_url`."""
    return reverse_lazy('v1:quickbooks-auth-get-authorization-url')


def get_process_auth_callback():
    """Get url for `process_auth_callback`."""
    return reverse_lazy('v1:quickbooks-auth-process-auth-callback')


class TestNotAuthenticatedAPI:
    """Test `QuickBooksAuthorizationView` api for not authenticated users.

    Only some of methods should be available for not authenticated users.

    """
    success_url = 'http://success.com'
    error_url = 'http://error.com'

    def _set_fake_cache_data(self, state_token: str):
        """Shortcut to set fake user data in redis cache."""
        cache.set(
            state_token,
            {
                'user_id': 1,
                'success_url': self.success_url,
                'error_url': self.error_url,
            },
            100
        )

    @pytest.mark.parametrize(
        argnames='url,method',
        argvalues=(
            (get_authorization_url, 'get'),
        ),
    )
    def test_quickbooks_options_access(
        self, api_client: APIClient, url, method
    ):
        """Test access to QuickBooksAuthorizationView."""
        method = getattr(api_client, method)
        response = method(url())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_process_auth_callback_denied_invalid_state_token(
        self, api_client: APIClient
    ):
        """Test access to QuickBooksAuthorizationView `process_auth_callback`.

        Check that case when user declines app access request and `state` token
        doesn't exist in cache there is returned base error url.

        """
        expected_url = str(settings.QUICKBOOKS['BASE_AUTH_ERROR_REDIRECT_URL'])
        # set fake data in cache to pass validation
        state_token = str(uuid.uuid4())
        url = get_process_auth_callback()
        params = {
            'error': 'access_denied',
            'state': state_token,
        }
        response = api_client.get(url, data=params)
        assert response.status_code == status.HTTP_302_FOUND
        assert expected_url == response.get('Location')

    def test_process_auth_callback_denied(self, api_client: APIClient):
        """Test access to QuickBooksAuthorizationView `process_auth_callback`.

        Check that case when user declines app access request is correctly
        handled.

        """
        # set fake data in cache to pass validation
        state_token = str(uuid.uuid4())
        self._set_fake_cache_data(state_token)

        url = get_process_auth_callback()
        params = {
            'error': 'access_denied',
            'state': state_token,
        }
        response = api_client.get(url, data=params)
        assert response.status_code == status.HTTP_302_FOUND
        assert self.error_url == response.get('Location')

    def test_process_auth_callback_approved_invalid_state_token(
        self, api_client: APIClient
    ):
        """Test access to QuickBooksAuthorizationView `process_auth_callback`.

        Check that case when user approves app access request and `state` token
        doesn't exist in cache there is returned base error url.

        """
        expected_url = str(settings.QUICKBOOKS['BASE_AUTH_ERROR_REDIRECT_URL'])
        # set fake data in cache to pass validation
        state_token = str(uuid.uuid4())
        url = get_process_auth_callback()
        params = {
            'code': str(uuid.uuid4()),
            'realmId': str(uuid.uuid4()),
            'state': state_token,
        }
        response = api_client.get(url, data=params)
        assert response.status_code == status.HTTP_302_FOUND
        assert expected_url == response.get('Location')

    def test_process_auth_callback_approved(
        self, api_client: APIClient, mocker
    ):
        """Test access to QuickBooksAuthorizationView `process_auth_callback`.

        Check that case when user approves app access request is correctly
        handled.

        """
        # set fake data in cache to pass validation
        state_token = str(uuid.uuid4())
        self._set_fake_cache_data(state_token)
        cache_set = mocker.patch('django.core.cache.cache.set')

        url = get_process_auth_callback()
        params = {
            'code': str(uuid.uuid4()),
            'realmId': str(uuid.uuid4()),
            'state': state_token,
        }
        response = api_client.get(url, data=params)
        assert response.status_code == status.HTTP_302_FOUND
        assert self.success_url in response.get('Location')
        cache_set.assert_called()

    def test_process_auth_callback_approved_error(
        self, api_client: APIClient, mocker
    ):
        """Test access to QuickBooksAuthorizationView `process_auth_callback`.

        Check that case when user approves app access request, but gets error
        during getting `bearer token` correctly handled.

        """
        # set fake data in cache to pass validation
        state_token = str(uuid.uuid4())
        self._set_fake_cache_data(state_token)
        mocker.patch(
            'libs.quickbooks.clients.QuickBooksTestClient.get_bearer_token',
            side_effect=AuthClientError(MagicMock(
                status_code=400,
                content='1',
                headers={}
            ))
        )

        cache_set = mocker.patch('django.core.cache.cache.set')

        url = get_process_auth_callback()
        params = {
            'code': str(uuid.uuid4()),
            'realmId': str(uuid.uuid4()),
            'state': state_token,
        }
        response = api_client.get(url, data=params)
        assert response.status_code == status.HTTP_302_FOUND
        assert self.error_url in response.get('Location')
        cache_set.assert_not_called()


class TestClientUserAPI:
    """Test `QuickBooksAuthorizationView` api for client users.

    Clients can't have access to this API.

    """

    @pytest.mark.parametrize(
        argnames='url,method',
        argvalues=(
            (get_authorization_url, 'get'),
        ),
    )
    def test_quickbooks_options_access(
        self, auth_client_api: APIClient, url, method
    ):
        """Test access to QuickBooksOptionsView."""
        method = getattr(auth_client_api, method)
        response = method(url())
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAttorneyUserAPI:
    """Test `QuickBooksAuthorizationView` api for attorney users.

    Attorneys have access to this API.

    """

    def test_get_authorization_url(
        self, auth_attorney_api: APIClient, mocker
    ):
        """Test `get_authorization_url` method works correctly."""
        cache_set = mocker.patch('django.core.cache.cache.set')
        expected_url = default_quickbooks_client().get_authorization_url()
        url = get_authorization_url()
        params = {
            'success_url': 'http://test.com',
            'error_url': 'http://test.com'
        }
        response = auth_attorney_api.get(url, data=params)
        # check response and results
        assert response.status_code == status.HTTP_200_OK
        assert response.data['url'] == expected_url
        cache_set.assert_called()
