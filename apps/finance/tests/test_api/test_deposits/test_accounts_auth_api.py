import uuid

from django.test import override_settings
from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import FORBIDDEN, FOUND, OK, UNAUTHORIZED

from apps.finance.factories import FinanceProfileFactory
from apps.finance.models import AccountProxy
from apps.users.models import Attorney


def get_authorization_url():
    """Get url for `get_authorization_link` method."""
    return reverse_lazy('v1:deposits-auth-get-authorization-link')


def get_callback_url():
    """Get url for `process_auth_callback` method."""
    return reverse_lazy('v1:deposits-auth-process-auth-callback')


class TestClientUserAPI:
    """Test `AccountAuthViewSet` api for client users."""

    def test_get_authorization_url(self, auth_client_api: APIClient):
        """Test access is forbidden to `get_authorization_link` API method."""
        url = get_authorization_url()
        response = auth_client_api.get(url)
        assert response.status_code == FORBIDDEN

    def test_process_auth_callback(self, auth_client_api: APIClient):
        """Test access is allowed to `process_auth_callback` API method."""
        url = get_callback_url()
        response = auth_client_api.get(url)
        assert response.status_code == FOUND


class TestAttorneyUserAPI:
    """Test `AccountAuthViewSet` api for attorney users."""

    def test_get_authorization_url_no_finance_profile(
        self, auth_attorney_api: APIClient, mocker
    ):
        """Test access is denied when attorney has no finance profile."""
        mocker.patch('django.core.cache.cache.set')
        url = get_authorization_url()
        response = auth_attorney_api.get(url, data=dict(
            error_url='http://test.ru', success_url='http://test.ru'
        ))
        assert response.status_code == FORBIDDEN

    def test_get_authorization_url_with_existing_deposit_account(
        self, auth_attorney_api: APIClient, attorney: Attorney, mocker
    ):
        """Test access is denied when attorney already has connected account.
        """
        FinanceProfileFactory(user=attorney.user)
        mocker.patch('django.core.cache.cache.set')
        url = get_authorization_url()
        response = auth_attorney_api.get(url, data=dict(
            error_url='http://test.ru', success_url='http://test.ru'
        ))
        assert response.status_code == FORBIDDEN

    def test_get_authorization_url(
        self, auth_attorney_api: APIClient, attorney: Attorney, mocker
    ):
        """Test access is allowed when attorney has no deposit account yet."""
        FinanceProfileFactory(user=attorney.user, deposit_account=None)
        cache_set = mocker.patch('django.core.cache.cache.set')
        url = get_authorization_url()
        response = auth_attorney_api.get(url, data=dict(
            error_url='http://test.ru', success_url='http://test.ru'
        ))
        assert response.status_code == OK
        assert 'url' in response.data
        cache_set.assert_called()

    def test_process_auth_callback(self, auth_client_api: APIClient):
        """Test access is allowed to `process_auth_callback` API method."""
        url = get_callback_url()
        response = auth_client_api.get(url)
        assert response.status_code == FOUND


class TestNotAuthenticatedAPI:
    """Test `AccountAuthViewSet` api for not authenticated users."""

    base_error_url = 'http://error.com'
    valid_success_data = {'code': 'test', 'state': 'test'}
    valid_error_data = {
        'error': 'test', 'error_description': 'test', 'state': 'test'
    }
    valid_callback_data = (valid_success_data, valid_error_data)

    def test_get_authorization_url(self, api_client: APIClient):
        """Test access is forbidden to `get_authorization_link` API method."""
        response = api_client.get(get_authorization_url())
        assert response.status_code == UNAUTHORIZED

    @override_settings(STRIPE_BASE_AUTH_ERROR_REDIRECT_URL=base_error_url)
    @pytest.mark.parametrize(
        argnames='data,',
        argvalues=({}, {'error': 'error'}),
    )
    def test_process_auth_callback_invalid_data(
        self, api_client: APIClient, data: dict
    ):
        """Test `process_auth_callback` on invalid data redirects to error."""
        response = api_client.get(get_callback_url(), data=data)
        # check that returned data is correct
        assert response.status_code == FOUND
        assert self.base_error_url == response.get('Location')

    @override_settings(STRIPE_BASE_AUTH_ERROR_REDIRECT_URL=base_error_url)
    @pytest.mark.parametrize(
        argnames='data,',
        argvalues=valid_callback_data
    )
    def test_process_auth_callback_no_state_info(
        self, api_client: APIClient, data: dict
    ):
        """Test on valid data but without `state_info` redirects to error."""
        response = api_client.get(get_callback_url(), data=data)
        # check that returned data is correct
        assert response.status_code == FOUND
        assert self.base_error_url == response.get('Location')

    @override_settings(STRIPE_BASE_AUTH_ERROR_REDIRECT_URL=base_error_url)
    @pytest.mark.parametrize(
        argnames='data,',
        argvalues=valid_callback_data
    )
    def test_process_auth_callback_no_user(
        self, api_client: APIClient, data: dict, mocker
    ):
        """Test on valid data, `state_info` and absent user redirects to error.
        """
        cache_get = mocker.patch(
            'django.core.cache.cache.get',
            return_value=self._cache_get_return_value(0)
        )
        response = api_client.get(get_callback_url(), data=data)
        # check that returned data is correct and all required methods called
        assert response.status_code == FOUND
        assert 'http://cache-error.com' == response.get('Location')
        cache_get.assert_called()

    @override_settings(STRIPE_BASE_AUTH_ERROR_REDIRECT_URL=base_error_url)
    def test_process_auth_error_callback(
        self, api_client: APIClient, attorney: Attorney, mocker
    ):
        """Test on all valid data for error callback redirects to error."""
        cache_get = mocker.patch(
            'django.core.cache.cache.get',
            return_value=self._cache_get_return_value(attorney.user_id)
        )
        response = api_client.get(
            get_callback_url(), data=self.valid_error_data
        )
        # check that returned data is correct and all required methods called
        assert response.status_code == FOUND
        assert 'http://cache-error.com' == response.get('Location')
        cache_get.assert_called()

    @override_settings(STRIPE_BASE_AUTH_ERROR_REDIRECT_URL=base_error_url)
    def test_process_auth_success_callback_no_finance_profile(
        self, api_client: APIClient, attorney: Attorney, mocker
    ):
        """Test on all valid data for success callback with no finance profile.

        When attorney has no FinanceProfile user should be redirected to error
        url.

        """
        cache_get = mocker.patch(
            'django.core.cache.cache.get',
            return_value=self._cache_get_return_value(attorney.user_id)
        )
        response = api_client.get(
            get_callback_url(), data=self.valid_success_data
        )

        # check that returned data is correct and all required methods called
        expected_url = (
            'http://cache-error.com?error=AppUser has no finance_profile.'
        )
        assert response.status_code == FOUND
        assert expected_url == response.get('Location')
        cache_get.assert_called()

    @override_settings(STRIPE_BASE_AUTH_ERROR_REDIRECT_URL=base_error_url)
    def test_process_auth_success_callback_deposit_account_already_exists(
        self, api_client: APIClient, attorney: Attorney, mocker
    ):
        """Test on all valid data for success callback.

        When attorney has FinanceProfile with already existing
        `deposit_account`, user should be redirected to error url.

        """
        FinanceProfileFactory(user=attorney.user)
        cache_get = mocker.patch(
            'django.core.cache.cache.get',
            return_value=self._cache_get_return_value(attorney.user_id)
        )
        response = api_client.get(
            get_callback_url(), data=self.valid_success_data
        )

        # check that returned data is correct and all required methods called
        expected_url = (
            f'http://cache-error.com?error=User {attorney.user} already has '
            f'deposit account'
        )
        assert response.status_code == FOUND
        assert expected_url == response.get('Location')
        cache_get.assert_called()

    @override_settings(STRIPE_BASE_AUTH_ERROR_REDIRECT_URL=base_error_url)
    def test_process_auth_success_callback_error_in_get_token(
        self, api_client: APIClient, attorney: Attorney, mocker
    ):
        """Test on all valid data for success callback.

        When there appears some Exception in
        `stripe_deposits_service.get_token`, user should be redirected to error
        url.

        """
        FinanceProfileFactory(user=attorney.user, deposit_account=None)
        cache_get = mocker.patch(
            'django.core.cache.cache.get',
            return_value=self._cache_get_return_value(attorney.user_id)
        )
        get_token = mocker.patch(
            'apps.finance.services.deposits.StripeDepositsService.get_token',
            side_effect=ValueError('Problem')
        )

        response = api_client.get(
            get_callback_url(), data=self.valid_success_data
        )

        # check that returned data is correct and all required methods called
        expected_url = 'http://cache-error.com?error=Problem'
        assert response.status_code == FOUND
        assert expected_url == response.get('Location')
        cache_get.assert_called()
        get_token.assert_called()

    @override_settings(STRIPE_BASE_AUTH_ERROR_REDIRECT_URL=base_error_url)
    def test_process_auth_success_callback_error_in_get_connected_account(
        self, api_client: APIClient, attorney: Attorney, mocker
    ):
        """Test on all valid data for success callback.

        When there appears some Exception in
        `Account.objects.get_connected_account_from_token`, user should be
        redirected to error url.

        """
        FinanceProfileFactory(user=attorney.user, deposit_account=None)
        cache_get = mocker.patch(
            'django.core.cache.cache.get',
            return_value=self._cache_get_return_value(attorney.user_id)
        )
        get_token = mocker.patch(
            'apps.finance.services.deposits.StripeDepositsService.get_token',
            return_value={'access_token': '123'}
        )
        get_account = mocker.patch(
            'djstripe.models.Account.get_connected_account_from_token',
            side_effect=ValueError('Problem')
        )

        response = api_client.get(
            get_callback_url(), data=self.valid_success_data
        )

        # check that returned data is correct and all required methods called
        expected_url = 'http://cache-error.com?error=Problem'
        assert response.status_code == FOUND
        assert expected_url == response.get('Location')
        cache_get.assert_called()
        get_token.assert_called()
        get_account.assert_called()

    @override_settings(STRIPE_BASE_AUTH_ERROR_REDIRECT_URL=base_error_url)
    def test_process_auth_success_callback(
        self, api_client: APIClient, attorney: Attorney, mocker
    ):
        """Test on all valid data for success callback."""
        FinanceProfileFactory(user=attorney.user, deposit_account=None)
        if not hasattr(attorney.user, 'finance_profile'):
            FinanceProfileFactory(user=attorney.user)
        cache_get = mocker.patch(
            'django.core.cache.cache.get',
            return_value=self._cache_get_return_value(attorney.user_id)
        )
        get_token = mocker.patch(
            'apps.finance.services.deposits.StripeDepositsService.get_token',
            return_value={'access_token': '123'}
        )
        fake_account = AccountProxy.objects.create(
            id=str(uuid.uuid4()),
            charges_enabled=True,
            details_submitted=True,
            payouts_enabled=True
        )
        get_account = mocker.patch(
            'djstripe.models.Account.get_connected_account_from_token',
            return_value=fake_account
        )
        resync_account = mocker.patch(
            'apps.finance.models.AccountProxy.resync',
            return_value=fake_account
        )
        notify_user = mocker.patch(
            'apps.finance.models.AccountProxy.notify_user',
        )

        response = api_client.get(
            get_callback_url(), data=self.valid_success_data
        )
        attorney.refresh_from_db()

        # check that returned data is correct and all required methods called
        assert response.status_code == FOUND
        assert 'http://success.com' == response.get('Location')
        assert attorney.deposit_account.id == fake_account.id
        cache_get.assert_called()
        get_token.assert_called()
        get_account.assert_called()
        resync_account.assert_called()
        notify_user.assert_called()

    def _cache_get_return_value(self, user_id):
        return {
            'error_url': 'http://cache-error.com',
            'success_url': 'http://success.com',
            'user_id': user_id,
        }
