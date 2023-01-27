from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest
from stripe.error import InvalidRequestError

from libs.testing.constants import BAD_REQUEST, FORBIDDEN, NOT_FOUND, OK

from apps.users.factories import AttorneyVerifiedFactory


def get_url():
    """Get url for current user `stripe profile`."""
    return reverse_lazy('v1:current-customer')


class TestClientUserAPI:
    """Test `current stripe profile` api for auth users.

    Clients can't have access to this API.

    """

    @pytest.mark.parametrize(
        argnames='method,',
        argvalues=(
            'get',
            'put',
            'patch'
        ),
    )
    def test_current_customer_access(
        self, auth_client_api: APIClient, method: str
    ):
        """Test access to `update` and `retrieve` API methods."""
        url = get_url()
        response = getattr(auth_client_api, method)(url)
        assert response.status_code == FORBIDDEN


class TestAttorneyUserAPI:
    """Test `current stripe profile` api for auth users.

    Attorneys can `retrieve` and `update` their stripe profile.

    """

    @pytest.mark.parametrize(
        argnames='method,',
        argvalues=(
            'get',
            'put',
            'patch'
        ),
    )
    def test_current_customer_access_no_customer(
        self, api_client: APIClient, method: str
    ):
        """Test access to `update` and `retrieve` API methods.

        When attorney has no stripe `customer` in DB, he can't work with his
        stripe profile and should get 404 error.

        """
        url = get_url()
        attorney = AttorneyVerifiedFactory()
        api_client.force_authenticate(user=attorney.user)
        response = getattr(api_client, method)(url)
        assert response.status_code == NOT_FOUND

    def test_retrieve_current_customer(self, customer, api_client: APIClient):
        """Test `retrieve` current stripe profile by attorney with customer.
        """
        url = get_url()
        api_client.force_authenticate(user=customer.subscriber)
        response = api_client.get(url)
        assert response.status_code == OK
        assert response.data['id'] == customer.id

    def test_update_current_customer_no_payment_method(
        self, customer, api_client: APIClient, mocker
    ):
        """Test `update` current stripe profile by attorney with customer.

        Check that when `payment_method` field is not defined in params, no
        `add_payment_method` would be called.

        """
        add_payment_method = mocker.patch(
            'apps.finance.models.CustomerProxy.add_payment_method'
        )
        url = get_url()
        api_client.force_authenticate(user=customer.subscriber)
        response = api_client.put(url)
        assert response.status_code == OK
        assert response.data['id'] == customer.id
        add_payment_method.assert_not_called()

    def test_update_current_customer_error_in_add_payment_method(
        self, customer, api_client: APIClient, mocker
    ):
        """Test `update` current stripe profile by attorney with customer.

        Check that when there is an error in `add_payment_method` -
        ValidationError would be raised.

        """
        mocker.patch(
            'apps.finance.models.CustomerProxy.add_payment_method',
            side_effect=InvalidRequestError(param=None, message=None)
        )
        url = get_url()
        api_client.force_authenticate(user=customer.subscriber)
        response = api_client.put(url, data={'payment_method': 'test'})
        assert response.status_code == BAD_REQUEST

    def test_update_current_customer(
        self, customer, api_client: APIClient, mocker
    ):
        """Test `update` current stripe profile by attorney with customer.

        Check that update works correctly when `payment_method` is set and
        `add_payment_method` processed successfully.

        """
        add_payment_method = mocker.patch(
            'apps.finance.models.CustomerProxy.add_payment_method',
        )
        url = get_url()
        api_client.force_authenticate(user=customer.subscriber)
        response = api_client.put(url, data={'payment_method': 'test'})
        assert response.status_code == OK
        assert response.data['id'] == customer.id
        add_payment_method.assert_called()
