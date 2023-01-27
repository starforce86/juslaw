from unittest.mock import MagicMock

from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import arrow
import pytest
from quickbooks.exceptions import ObjectNotFoundException


def get_customers_url():
    """Get url for `get_customers`."""
    return reverse_lazy('v1:quickbooks-export-get-customers')


def start_export_url():
    """Get url for `export`."""
    return reverse_lazy('v1:quickbooks-export-export')


class TestNotAuthenticatedAPI:
    """Test `QuickBooksExportView` api for not authenticated users.

    Not authenticated users can't have access to this API.

    """

    @pytest.mark.parametrize(
        argnames='url,method',
        argvalues=(
            (get_customers_url, 'get'),
            (start_export_url, 'post'),
        ),
    )
    def test_quickbooks_export_access(
        self, api_client: APIClient, url, method
    ):
        """Test access to QuickBooksExportView."""
        method = getattr(api_client, method)
        response = method(url())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestClientUserAPI:
    """Test `QuickBooksExportView` api for client users.

    Clients can't have access to this API.

    """

    @pytest.mark.parametrize(
        argnames='url,method',
        argvalues=(
            (get_customers_url, 'get'),
            (start_export_url, 'post'),
        ),
    )
    def test_quickbooks_export_access(
        self, auth_client_api: APIClient, url, method
    ):
        """Test access to QuickBooksExportView."""
        method = getattr(auth_client_api, method)
        response = method(url())
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAttorneyUserAPI:
    """Test `QuickBooksExportView` api for attorney users.

    Attorneys have access to this API.

    """

    @pytest.mark.parametrize(
        argnames='url,method',
        argvalues=(
            (get_customers_url, 'get'),
            (start_export_url, 'post'),
        ),
    )
    def test_export_methods_no_auth_tokens_in_cache(
        self, url, method, auth_attorney_api: APIClient,
        invoice_with_time_billing, mocker
    ):
        """Test that export methods raise errors when no QuickBooks auth is set
        """
        mocker.patch(
            'libs.quickbooks.clients.QuickBooksTestClient._get_auth_client',
            return_value=MagicMock(
                realm_id=None,
                access_token=None,
                refresh_token=None,
            )
        )
        method = getattr(auth_attorney_api, method)
        response = method(
            url(), data={'invoice': invoice_with_time_billing.id}
        )
        # check response and results
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Not authenticated in QuickBooks' in str(response.data)

    @pytest.mark.parametrize(
        argnames='url,method',
        argvalues=(
            (get_customers_url, 'get'),
            (start_export_url, 'post'),
        ),
    )
    def test_export_methods_expired_token(
        self, url, method, auth_attorney_api: APIClient,
        invoice_with_time_billing, mocker
    ):
        """Test that export methods raise errors when QB token is expired.
        """
        mocker.patch(
            'libs.quickbooks.clients.QuickBooksTestClient._get_auth_client',
            return_value=MagicMock(
                expires_in=arrow.utcnow().timestamp - 3600,
                x_refresh_token_expires_in=arrow.utcnow().timestamp - 3600,
            )
        )
        method = getattr(auth_attorney_api, method)
        response = method(
            url(), data={'invoice': invoice_with_time_billing.id}
        )
        # check response and results
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Refresh token is expired' in str(response.data)

    def test_get_customers(self, auth_attorney_api: APIClient,):
        """Test that `get_customers` API method works correctly."""
        response = auth_attorney_api.get(get_customers_url())
        # check response and results
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['email'] == 'Birds@Intuit.com'

    def test_export_invoice_without_time_billings(
        self, auth_attorney_api: APIClient, invoice_no_time_billing, mocker
    ):
        """Test error raised for export of `invoice` without time billings."""
        response = auth_attorney_api.post(
            start_export_url(),
            data={'invoice': invoice_no_time_billing.id, 'customer': 1}
        )
        # check response and results
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invoice should have time billings' in str(response.data)

    def test_export_not_valid_customer(
        self, auth_attorney_api: APIClient, invoice_with_time_billing, mocker
    ):
        """Test error raised for export with not valid customer (`export`)."""
        mocker.patch(
            'libs.quickbooks.clients.QuickBooksTestClient._qb_class_get',
            side_effect=ObjectNotFoundException('Error')
        )
        response = auth_attorney_api.post(
            start_export_url(),
            data={'invoice': invoice_with_time_billing.id, 'customer': 1}
        )
        # check response and results
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Customer not found in QuickBooks' in str(response.data)

    @pytest.mark.parametrize(
        argnames='customer',
        argvalues=(1, None),
    )
    def test_export(
        self, customer, auth_attorney_api: APIClient,
        invoice_with_time_billing, mocker
    ):
        """Test `export` works correctly independent on `customer` existence.
        """
        sync_invoice = mocker.patch(
            'apps.accounting.services.utils.sync_invoice'
        )
        response = auth_attorney_api.post(
            start_export_url(),
            data={
                'invoice': invoice_with_time_billing.id,
                'customer': customer
            }
        )
        # check response and results
        assert response.status_code == status.HTTP_200_OK
        sync_invoice.assert_called()
