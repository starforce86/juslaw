from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import FORBIDDEN, NOT_FOUND, OK, UNAUTHORIZED

from apps.finance.factories import FinanceProfileFactory
from apps.users.models import Attorney

from ....models import AccountProxyInfo


def get_current_account():
    """Get url for `get_current` method."""
    return reverse_lazy('v1:current-account-get-current')


def get_login_url():
    """Get url for `get_login_link` method."""
    return reverse_lazy('v1:current-account-get-login-link')


class TestClientUserAPI:
    """Test `CurrentAccountViewSet` api for client users."""

    @pytest.mark.parametrize(
        argnames='url,',
        argvalues=(
            get_login_url(),
            get_current_account()
        ),
    )
    def test_get_methods(self, auth_client_api: APIClient, url: str):
        """Test access to CurrentAccountViewSet API for clients."""
        response = auth_client_api.get(url)
        assert response.status_code == FORBIDDEN


class TestNotAuthenticatedAPI:
    """Test `CurrentAccountViewSet` api for not authenticated users."""

    @pytest.mark.parametrize(
        argnames='url,',
        argvalues=(
            get_login_url(),
            get_current_account()
        ),
    )
    def test_get_methods(self, api_client: APIClient, url: str):
        """Test access to CurrentAccountViewSet API for not authorized users.
        """
        response = api_client.get(url)
        assert response.status_code == UNAUTHORIZED


class TestAttorneyUserAPI:
    """Test `CurrentAccountViewSet` api for attorney users."""

    @pytest.mark.parametrize(
        argnames='url,',
        argvalues=(
            get_login_url(),
            get_current_account()
        ),
    )
    def test_get_methods_no_finance_profile(
        self, auth_attorney_api: APIClient, url: str, attorney: Attorney
    ):
        """Test access to CurrentAccountViewSet API for attorneys.

        When attorney has no `finance_profile` - there is returned 404 response

        """
        if hasattr(attorney.user, 'finance_profile'):
            attorney.user.finance_profile = None
            attorney.user.save()
        response = auth_attorney_api.get(url)
        assert response.status_code == NOT_FOUND

    @pytest.mark.parametrize(
        argnames='url,',
        argvalues=(
            get_login_url(),
            get_current_account()
        ),
    )
    def test_get_methods_no_deposit_account(
        self, auth_attorney_api: APIClient, url: str, attorney: Attorney
    ):
        """Test access to CurrentAccountViewSet API for attorneys.

        When attorney has `finance_profile` without defined `deposit_account`
        - there is returned 404 response.

        """
        FinanceProfileFactory(user=attorney.user, deposit_account=None)
        response = auth_attorney_api.get(url)
        assert response.status_code == NOT_FOUND

    def test_get_current_with_no_info(
        self, auth_attorney_api: APIClient, attorney: Attorney
    ):
        """Test `get_current` API method when account has no `info`.

        When account has no `extra` info - `capabilities`,
        `bank_external_account`, `card_external_account` fields wouldn't be
        set.

        """
        FinanceProfileFactory(user=attorney.user)
        response = auth_attorney_api.get(get_current_account())
        assert response.status_code == OK
        assert response.data['capabilities'] is None
        assert response.data['bank_external_account'] is None
        assert response.data['card_external_account'] is None

    def test_get_current_with_info(
        self, auth_attorney_api: APIClient, attorney: Attorney
    ):
        """Test `get_current` API method when account has `info`.

        When account has `extra` info - `capabilities`, `bank_external_account`
        and `card_external_account` fields are correctly set.

        """
        profile = FinanceProfileFactory(user=attorney.user)
        AccountProxyInfo.objects.create(
            account=profile.deposit_account,
            capabilities={'1': 1},
            external_accounts={
                'data': [
                    {'object': 'card', 1: 1},
                    {'object': 'bank_account', 2: 2},
                ]
            }
        )
        response = auth_attorney_api.get(get_current_account())
        assert response.status_code == OK
        assert response.data['capabilities'] == {'1': 1}
        assert response.data['bank_external_account'] == \
            {'object': 'bank_account', 2: 2}
        assert response.data['card_external_account'] == \
            {'object': 'card', 1: 1}

    def test_get_login_url(
        self, auth_attorney_api: APIClient, attorney: Attorney, mocker
    ):
        """Test `get_login_link` API method."""
        mocker.patch(
            'apps.finance.models.AccountProxy.login_url',
            'http://test.com'
        )
        FinanceProfileFactory(user=attorney.user)
        response = auth_attorney_api.get(get_login_url())
        assert response.status_code == OK
        assert response.data['url'] == 'http://test.com'
