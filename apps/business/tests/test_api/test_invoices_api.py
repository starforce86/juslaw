from unittest.mock import patch

from django.urls import reverse_lazy
from django.utils import timezone

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import (
    BAD_REQUEST,
    CREATED,
    FORBIDDEN,
    NO_CONTENT,
    NOT_FOUND,
    OK,
)

from ....users.models import AppUser, Attorney, Support
from ... import factories, models
from ...api import serializers


def get_list_url():
    """Get url for invoice list retrieval."""
    return reverse_lazy('v1:invoices-list')


def get_detail_url(invoice: models.Invoice):
    """Get url for invoice details retrieval."""
    return reverse_lazy('v1:invoices-detail', kwargs={'pk': invoice.pk})


def get_invoice_export(invoice: models.Invoice):
    """Get url for invoice file export."""
    return reverse_lazy('v1:invoices-export', kwargs={'pk': invoice.pk})


def get_invoice_sent(invoice: models.Invoice):
    """Get url for invoice file sending."""
    return reverse_lazy('v1:invoices-send', kwargs={'pk': invoice.pk})


@pytest.fixture(scope='session')
def attorney_open_invoice(
    django_db_blocker, matter: models.Matter, attorney: Attorney
) -> models.Invoice:
    """Create pending invoice(created by attorney) for testing."""
    with django_db_blocker.unblock():
        return factories.InvoiceWithTBFactory(
            matter=matter,
            created_by_id=attorney.pk,
            status=models.Invoice.INVOICE_STATUS_OPEN
        )


@pytest.fixture(scope='session')
def support_open_invoice(
    django_db_blocker, matter: models.Matter, support: Support
) -> models.Invoice:
    """Create pending invoice(created by support) for testing."""
    with django_db_blocker.unblock():
        return factories.InvoiceWithTBFactory(
            matter=matter,
            created_by_id=support.pk,
            status=models.Invoice.INVOICE_STATUS_OPEN
        )


@pytest.fixture(scope='session')
def shared_attorney_open_invoice(
    django_db_blocker, matter: models.Matter, shared_attorney: Attorney
) -> models.Invoice:
    """Create pending invoice(created by shared_attorney) for testing."""
    with django_db_blocker.unblock():
        return factories.InvoiceWithTBFactory(
            matter=matter,
            created_by_id=shared_attorney.pk,
            status=models.Invoice.INVOICE_STATUS_OPEN
        )


@pytest.fixture(scope='session')
def attorney_sent_invoice(
    django_db_blocker, matter: models.Matter, attorney: Attorney
) -> models.Invoice:
    """Create sent invoice(created by attorney) for testing."""
    with django_db_blocker.unblock():
        return factories.InvoiceWithTBFactory(
            matter=matter,
            created_by_id=attorney.pk,
            status=models.Invoice.INVOICE_STATUS_SENT
        )


@pytest.fixture(scope='session')
def support_sent_invoice(
    django_db_blocker, matter: models.Matter, support: Support
) -> models.Invoice:
    """Create sent invoice(created by support) for testing."""
    with django_db_blocker.unblock():
        return factories.InvoiceWithTBFactory(
            matter=matter,
            created_by_id=support.pk,
            status=models.Invoice.INVOICE_STATUS_SENT
        )


@pytest.fixture(scope='session')
def shared_attorney_sent_invoice(
    django_db_blocker, matter: models.Matter, shared_attorney: Attorney
) -> models.Invoice:
    """Create sent invoice(created by shared_attorney) for testing."""
    with django_db_blocker.unblock():
        return factories.InvoiceWithTBFactory(
            matter=matter,
            created_by_id=shared_attorney.pk,
            status=models.Invoice.INVOICE_STATUS_SENT
        )


@pytest.fixture(scope='session')
def attorney_to_be_paid_invoice(
    django_db_blocker, matter: models.Matter, attorney: Attorney
) -> models.Invoice:
    """Create invoice which payment is in progress for testing.

    Created by attorney.

    """
    with django_db_blocker.unblock():
        return factories.ToBePaidInvoice(
            matter=matter, created_by_id=attorney.pk
        )


@pytest.fixture(scope='session')
def support_to_be_paid_invoice(
    django_db_blocker, matter: models.Matter, support: Support
) -> models.Invoice:
    """Create invoice which payment is in progress for testing.

    Created by support.

    """
    with django_db_blocker.unblock():
        return factories.ToBePaidInvoice(
            matter=matter, created_by_id=support.pk
        )


@pytest.fixture(scope='session')
def shared_attorney_to_be_paid_invoice(
    django_db_blocker, matter: models.Matter, shared_attorney: Attorney
) -> models.Invoice:
    """Create invoice which payment is in progress for testing.

    Created by shared_attorney.

    """
    with django_db_blocker.unblock():
        return factories.ToBePaidInvoice(
            matter=matter, created_by_id=shared_attorney.pk
        )


@pytest.fixture(scope='session')
def attorney_paid_invoice(
    django_db_blocker, matter: models.Matter, attorney: Attorney
) -> models.Invoice:
    """Create paid invoice(created by attorney) for testing."""
    with django_db_blocker.unblock():
        return factories.PaidInvoiceFactory(
            matter=matter, created_by_id=attorney.pk
        )


@pytest.fixture(scope='session')
def support_paid_invoice(
    django_db_blocker, matter: models.Matter, support: Support
) -> models.Invoice:
    """Create paid invoice(created by support) for testing."""
    with django_db_blocker.unblock():
        return factories.PaidInvoiceFactory(
            matter=matter, created_by_id=support.pk
        )


@pytest.fixture(scope='session')
def shared_attorney_paid_invoice(
    django_db_blocker, matter: models.Matter, shared_attorney: Attorney
) -> models.Invoice:
    """Create paid invoice(created by shared_attorney) for testing."""
    with django_db_blocker.unblock():
        return factories.PaidInvoiceFactory(
            matter=matter, created_by_id=shared_attorney.pk
        )


@pytest.fixture
def invoice(
    request,
    attorney_pending_invoice: models.Invoice,
    attorney_sent_invoice: models.Invoice,
    attorney_paid_invoice: models.Invoice,
    attorney_to_be_paid_invoice: models.Invoice,
    support_pending_invoice: models.Invoice,
    support_sent_invoice: models.Invoice,
    support_paid_invoice: models.Invoice,
    support_to_be_paid_invoice: models.Invoice,
    shared_attorney_pending_invoice: models.Invoice,
    shared_attorney_sent_invoice: models.Invoice,
    shared_attorney_paid_invoice: models.Invoice,
    shared_attorney_to_be_paid_invoice: models.Invoice,
    other_invoice: models.Invoice,
) -> models.Invoice:
    """Fixture to parametrize invoice fixtures."""
    mapping = dict(
        attorney_pending_invoice=attorney_pending_invoice,
        attorney_sent_invoice=attorney_sent_invoice,
        attorney_paid_invoice=attorney_paid_invoice,
        attorney_to_be_paid_invoice=attorney_to_be_paid_invoice,
        support_pending_invoice=support_pending_invoice,
        support_sent_invoice=support_sent_invoice,
        support_paid_invoice=support_paid_invoice,
        support_to_be_paid_invoice=support_to_be_paid_invoice,
        shared_attorney_pending_invoice=shared_attorney_pending_invoice,
        shared_attorney_sent_invoice=shared_attorney_sent_invoice,
        shared_attorney_paid_invoice=shared_attorney_paid_invoice,
        shared_attorney_to_be_paid_invoice=shared_attorney_to_be_paid_invoice,
        other_invoice=other_invoice,
    )
    invoice = mapping[request.param]
    return invoice


class TestAuthUserAPI:
    """Test invoices api for authenticated users.

    Attorneys have full access for invoices within owned matters or shared
    with them matters.
    Clients have readonly access to invoice of their matters.
    Support have full access for invoices within shared matters.

    """

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney',
            # shared attorney and support
            'support',
            'shared_attorney',
        ),
        indirect=True
    )
    def test_get_list(self, api_client: APIClient, user: AppUser):
        """Test that users can get list of invoices."""
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == OK

        invoices_expected = set(
            models.Invoice.objects.available_for_user(
                user=user
            ).values_list('pk', flat=True)
        )
        invoices_result = set(
            invoice_data['id'] for invoice_data in response.data['results']
        )
        assert invoices_result == invoices_expected

    @pytest.mark.parametrize(
        argnames='user, invoice, status_code',
        argvalues=(
            # Client user cases
            # Attorney's invoices
            ('client', 'attorney_pending_invoice', NOT_FOUND),
            ('client', 'attorney_sent_invoice', OK),
            ('client', 'attorney_to_be_paid_invoice', OK),
            ('client', 'attorney_paid_invoice', OK),
            # Support's invoices
            ('client', 'support_pending_invoice', NOT_FOUND),
            ('client', 'support_sent_invoice', OK),
            ('client', 'support_to_be_paid_invoice', OK),
            ('client', 'support_paid_invoice', OK),
            # Shared attorney's invoices
            ('client', 'shared_attorney_pending_invoice', NOT_FOUND),
            ('client', 'shared_attorney_sent_invoice', OK),
            ('client', 'shared_attorney_to_be_paid_invoice', OK),
            ('client', 'shared_attorney_paid_invoice', OK),
            # Check that client can't access to foreign invoices
            ('client', 'other_invoice', NOT_FOUND),

            # Attorney user cases
            # Attorney's invoices
            ('attorney', 'attorney_pending_invoice', OK),
            ('attorney', 'attorney_sent_invoice', OK),
            ('attorney', 'attorney_to_be_paid_invoice', OK),
            ('attorney', 'attorney_paid_invoice', OK),
            # Support's invoices
            ('attorney', 'support_pending_invoice', OK),
            ('attorney', 'support_sent_invoice', OK),
            ('attorney', 'support_to_be_paid_invoice', OK),
            ('attorney', 'support_paid_invoice', OK),
            # Shared attorney's invoices
            ('attorney', 'shared_attorney_pending_invoice', OK),
            ('attorney', 'shared_attorney_sent_invoice', OK),
            ('attorney', 'shared_attorney_to_be_paid_invoice', OK),
            ('attorney', 'shared_attorney_paid_invoice', OK),
            # Check that attorney can't access to foreign invoices
            ('attorney', 'other_invoice', NOT_FOUND),

            # Shared attorney and Support users cases

            # Attorney's invoices
            ('support', 'attorney_pending_invoice', OK),
            ('support', 'attorney_sent_invoice', OK),
            ('support', 'attorney_to_be_paid_invoice', OK),
            ('support', 'attorney_paid_invoice', OK),
            # Support's invoices
            ('support', 'support_pending_invoice', OK),
            ('support', 'support_sent_invoice', OK),
            ('support', 'support_to_be_paid_invoice', OK),
            ('support', 'support_paid_invoice', OK),
            # Shared attorney's invoices
            ('support', 'shared_attorney_pending_invoice', OK),
            ('support', 'shared_attorney_sent_invoice', OK),
            ('support', 'shared_attorney_to_be_paid_invoice', OK),
            ('support', 'shared_attorney_paid_invoice', OK),
            # Check that support can't access to foreign invoices
            ('support', 'other_invoice', NOT_FOUND),

            # Attorney's invoices
            ('shared_attorney', 'attorney_pending_invoice', OK),
            ('shared_attorney', 'attorney_sent_invoice', OK),
            ('shared_attorney', 'attorney_to_be_paid_invoice', OK),
            ('shared_attorney', 'attorney_paid_invoice', OK),
            # Support's invoices
            ('shared_attorney', 'support_pending_invoice', OK),
            ('shared_attorney', 'support_sent_invoice', OK),
            ('shared_attorney', 'support_to_be_paid_invoice', OK),
            ('shared_attorney', 'support_paid_invoice', OK),
            # Shared attorney's invoices
            ('shared_attorney', 'shared_attorney_pending_invoice', OK),
            ('shared_attorney', 'shared_attorney_sent_invoice', OK),
            ('shared_attorney', 'shared_attorney_to_be_paid_invoice', OK),
            ('shared_attorney', 'shared_attorney_paid_invoice', OK),
            # Check that shared_attorney can't access to foreign invoices
            ('shared_attorney', 'other_invoice', NOT_FOUND),

        ),
        indirect=True
    )
    def test_get_detail_invoice(
        self, api_client: APIClient, user: AppUser, status_code: int,
        invoice: models.Invoice, matter: models.Matter
    ):
        """Test that users can get details of invoices."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        url = get_detail_url(invoice)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status_code, response.data
        if status_code != OK:
            return
        models.Invoice.objects.available_for_user(user=user).get(
            pk=response.data['id']
        )

    @pytest.mark.parametrize(
        argnames='user, invoice, status_code',
        argvalues=(
            # Client user cases
            # Attorney's invoices
            ('client', 'attorney_pending_invoice', NOT_FOUND),
            ('client', 'attorney_sent_invoice', OK),
            ('client', 'attorney_to_be_paid_invoice', OK),
            ('client', 'attorney_paid_invoice', OK),
            # Support's invoices
            ('client', 'support_pending_invoice', NOT_FOUND),
            ('client', 'support_sent_invoice', OK),
            ('client', 'support_to_be_paid_invoice', OK),
            ('client', 'support_paid_invoice', OK),
            # Shared attorney's invoices
            ('client', 'shared_attorney_pending_invoice', NOT_FOUND),
            ('client', 'shared_attorney_sent_invoice', OK),
            ('client', 'shared_attorney_to_be_paid_invoice', OK),
            ('client', 'shared_attorney_paid_invoice', OK),
            # Check that client can't access to foreign invoices
            ('client', 'other_invoice', NOT_FOUND),

            # Attorney user cases
            # Attorney's invoices
            ('attorney', 'attorney_pending_invoice', OK),
            ('attorney', 'attorney_sent_invoice', OK),
            ('attorney', 'attorney_to_be_paid_invoice', OK),
            ('attorney', 'attorney_paid_invoice', OK),
            # Support's invoices
            ('attorney', 'support_pending_invoice', OK),
            ('attorney', 'support_sent_invoice', OK),
            ('attorney', 'support_to_be_paid_invoice', OK),
            ('attorney', 'support_paid_invoice', OK),
            # Shared attorney's invoices
            ('attorney', 'shared_attorney_pending_invoice', OK),
            ('attorney', 'shared_attorney_sent_invoice', OK),
            ('attorney', 'shared_attorney_to_be_paid_invoice', OK),
            ('attorney', 'shared_attorney_paid_invoice', OK),
            # Check that attorney can't access to foreign invoices
            ('attorney', 'other_invoice', NOT_FOUND),

            # Shared attorney and Support users cases

            # Attorney's invoices
            ('support', 'attorney_pending_invoice', OK),
            ('support', 'attorney_sent_invoice', OK),
            ('support', 'attorney_to_be_paid_invoice', OK),
            ('support', 'attorney_paid_invoice', OK),
            # Support's invoices
            ('support', 'support_pending_invoice', OK),
            ('support', 'support_sent_invoice', OK),
            ('support', 'support_to_be_paid_invoice', OK),
            ('support', 'support_paid_invoice', OK),
            # Shared attorney's invoices
            ('support', 'shared_attorney_pending_invoice', OK),
            ('support', 'shared_attorney_sent_invoice', OK),
            ('support', 'shared_attorney_to_be_paid_invoice', OK),
            ('support', 'shared_attorney_paid_invoice', OK),
            # Check that support can't access to foreign invoices
            ('support', 'other_invoice', NOT_FOUND),

            # Attorney's invoices
            ('shared_attorney', 'attorney_pending_invoice', OK),
            ('shared_attorney', 'attorney_sent_invoice', OK),
            ('shared_attorney', 'attorney_to_be_paid_invoice', OK),
            ('shared_attorney', 'attorney_paid_invoice', OK),
            # Support's invoices
            ('shared_attorney', 'support_pending_invoice', OK),
            ('shared_attorney', 'support_sent_invoice', OK),
            ('shared_attorney', 'support_to_be_paid_invoice', OK),
            ('shared_attorney', 'support_paid_invoice', OK),
            # Shared attorney's invoices
            ('shared_attorney', 'shared_attorney_pending_invoice', OK),
            ('shared_attorney', 'shared_attorney_sent_invoice', OK),
            ('shared_attorney', 'shared_attorney_to_be_paid_invoice', OK),
            ('shared_attorney', 'shared_attorney_paid_invoice', OK),
            # Check that shared_attorney can't access to foreign invoices
            ('shared_attorney', 'other_invoice', NOT_FOUND),
        ),
        indirect=True
    )
    def test_export_invoice(
        self, api_client: APIClient, user: AppUser, status_code: int,
        invoice: models.Invoice, matter: models.Matter
    ):
        """Test that users can get pdf file of invoice."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        url = get_invoice_export(invoice)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status_code, response.data
        if status_code != OK:
            return

        # Check that file was attached to response
        today_date = timezone.now().strftime('%Y-%m-%d')
        content_disposition = f'attachment;filename="Invoice_{today_date}.pdf"'
        content_disposition_from_response = response.get('Content-Disposition')

        assert 'application/pdf; charset=utf-8' == response.get('Content-Type')
        assert content_disposition == content_disposition_from_response

    @pytest.mark.parametrize(
        argnames='user, invoice, status_code',
        argvalues=(
            # Client user cases
            # Attorney's invoices
            ('client', 'attorney_pending_invoice', NOT_FOUND),
            ('client', 'attorney_sent_invoice', FORBIDDEN),
            ('client', 'attorney_to_be_paid_invoice', BAD_REQUEST),
            ('client', 'attorney_paid_invoice', BAD_REQUEST),
            # Support's invoices
            ('client', 'support_pending_invoice', NOT_FOUND),
            ('client', 'support_sent_invoice', FORBIDDEN),
            ('client', 'support_to_be_paid_invoice', BAD_REQUEST),
            ('client', 'support_paid_invoice', BAD_REQUEST),
            # Shared attorney's invoices
            ('client', 'shared_attorney_pending_invoice', NOT_FOUND),
            ('client', 'shared_attorney_sent_invoice', FORBIDDEN),
            ('client', 'shared_attorney_to_be_paid_invoice', BAD_REQUEST),
            ('client', 'shared_attorney_paid_invoice', BAD_REQUEST),
            # Check that client can't access to foreign invoices
            ('client', 'other_invoice', NOT_FOUND),

            # Attorney user cases
            # Attorney's invoices
            ('attorney', 'attorney_pending_invoice', OK),
            ('attorney', 'attorney_sent_invoice', OK),
            ('attorney', 'attorney_to_be_paid_invoice', BAD_REQUEST),
            ('attorney', 'attorney_paid_invoice', BAD_REQUEST),
            # Support's invoices
            ('attorney', 'support_pending_invoice', OK),
            ('attorney', 'support_sent_invoice', OK),
            ('attorney', 'support_to_be_paid_invoice', BAD_REQUEST),
            ('attorney', 'support_paid_invoice', BAD_REQUEST),
            # Shared attorney's invoices
            ('attorney', 'shared_attorney_pending_invoice', OK),
            ('attorney', 'shared_attorney_sent_invoice', OK),
            ('attorney', 'shared_attorney_to_be_paid_invoice', BAD_REQUEST),
            ('attorney', 'shared_attorney_paid_invoice', BAD_REQUEST),
            # Check that attorney can't access to foreign invoices
            ('attorney', 'other_invoice', NOT_FOUND),

            # Shared attorney and Support users cases

            # Attorney's invoices
            ('support', 'attorney_pending_invoice', OK),
            ('support', 'attorney_sent_invoice', OK),
            ('support', 'attorney_to_be_paid_invoice', BAD_REQUEST),
            ('support', 'attorney_paid_invoice', BAD_REQUEST),
            # Support's invoices
            ('support', 'support_pending_invoice', OK),
            ('support', 'support_sent_invoice', OK),
            ('support', 'support_to_be_paid_invoice', BAD_REQUEST),
            ('support', 'support_paid_invoice', BAD_REQUEST),
            # Shared attorney's invoices
            ('support', 'shared_attorney_pending_invoice', OK),
            ('support', 'shared_attorney_sent_invoice', OK),
            ('support', 'shared_attorney_to_be_paid_invoice', BAD_REQUEST),
            ('support', 'shared_attorney_paid_invoice', BAD_REQUEST),
            # Check that support can't access to foreign invoices
            ('support', 'other_invoice', NOT_FOUND),

            # Attorney's invoices
            ('shared_attorney', 'attorney_pending_invoice', OK),
            ('shared_attorney', 'attorney_sent_invoice', OK),
            ('shared_attorney', 'attorney_to_be_paid_invoice', BAD_REQUEST),
            ('shared_attorney', 'attorney_paid_invoice', BAD_REQUEST),
            # Support's invoices
            ('shared_attorney', 'support_pending_invoice', OK),
            ('shared_attorney', 'support_sent_invoice', OK),
            ('shared_attorney', 'support_to_be_paid_invoice', BAD_REQUEST),
            ('shared_attorney', 'support_paid_invoice', BAD_REQUEST),
            # Shared attorney's invoices
            ('shared_attorney', 'shared_attorney_pending_invoice', OK),
            ('shared_attorney', 'shared_attorney_sent_invoice', OK),
            ('shared_attorney', 'shared_attorney_to_be_paid_invoice', BAD_REQUEST), # noqa
            ('shared_attorney', 'shared_attorney_paid_invoice', BAD_REQUEST),
            # Check that shared_attorney can't access to foreign invoices
            ('shared_attorney', 'other_invoice', NOT_FOUND),
        ),
        indirect=True
    )
    @patch('apps.business.services.invoices.InvoiceEmailNotification')
    def test_send_invoice(
        self,
        email_mock,
        api_client: APIClient,
        user: AppUser,
        status_code: int,
        invoice: models.Invoice,
        matter: models.Matter
    ):
        """Test that only attorney can send invoice by email."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        data = {
            'recipient_list': [
                'test.invoice1@test.com',
                'test.invoice2@test.com'
            ],
            'note': 'test invoice sending'
        }
        url = get_invoice_sent(invoice)

        api_client.force_authenticate(user=user)
        response = api_client.post(url, data)

        assert response.status_code == status_code

        if response.status_code != OK:
            return

        # Check that email was delivered
        email_mock.assert_called_once_with(
            invoice=invoice,
            recipient_list=data['recipient_list'],
            note=data['note'],
        )
        email_mock().send.assert_called_once()

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', CREATED),
            # shared attorney and support
            ('support', CREATED),
            ('shared_attorney', CREATED),
        ),
        indirect=True
    )
    def test_create_invoice(
        self, api_client: APIClient, user: AppUser, status_code: int,
        pending_invoice: models.Invoice
    ):
        """Test that attorney can create invoices, but clients not."""
        pending_invoice.matter.status = models.Matter.STATUS_ACTIVE
        pending_invoice.matter.save()
        data = serializers.InvoiceSerializer(instance=pending_invoice).data
        api_client.force_authenticate(user=user)
        response = api_client.post(get_list_url(), data)
        assert response.status_code == status_code, response.data

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'attorney',
            # shared attorney and support
            'support',
            'shared_attorney',
        ),
        indirect=True
    )
    def test_create_foreign_invoice(
        self, api_client: APIClient, other_invoice: models.Invoice,
        user: AppUser
    ):
        """Test users can't create invoices in another attorneys matters."""
        data = serializers.InvoiceSerializer(instance=other_invoice).data
        api_client.force_authenticate(user=user)
        resp = api_client.post(get_list_url(), data)
        assert resp.status_code == BAD_REQUEST

    @pytest.mark.parametrize(
        argnames='user, invoice, status_code',
        argvalues=(
            # Client user cases
            # Attorney's invoices
            ('client', 'attorney_pending_invoice', FORBIDDEN),
            ('client', 'attorney_sent_invoice', FORBIDDEN),
            ('client', 'attorney_to_be_paid_invoice', FORBIDDEN),
            ('client', 'attorney_paid_invoice', FORBIDDEN),
            # Support's invoices
            ('client', 'support_pending_invoice', FORBIDDEN),
            ('client', 'support_sent_invoice', FORBIDDEN),
            ('client', 'support_to_be_paid_invoice', FORBIDDEN),
            ('client', 'support_paid_invoice', FORBIDDEN),
            # Shared attorney's invoices
            ('client', 'shared_attorney_pending_invoice', FORBIDDEN),
            ('client', 'shared_attorney_sent_invoice', FORBIDDEN),
            ('client', 'shared_attorney_to_be_paid_invoice', FORBIDDEN),
            ('client', 'shared_attorney_paid_invoice', FORBIDDEN),
            # Check that client can't access to foreign invoices
            ('client', 'other_invoice', FORBIDDEN),

            # Attorney user cases
            # Attorney's invoices
            ('attorney', 'attorney_pending_invoice', OK),
            ('attorney', 'attorney_sent_invoice', OK),
            ('attorney', 'attorney_to_be_paid_invoice', FORBIDDEN),
            ('attorney', 'attorney_paid_invoice', FORBIDDEN),
            # Support's invoices
            ('attorney', 'support_pending_invoice', OK),
            ('attorney', 'support_sent_invoice', OK),
            ('attorney', 'support_to_be_paid_invoice', FORBIDDEN),
            ('attorney', 'support_paid_invoice', FORBIDDEN),
            # Shared attorney's invoices
            ('attorney', 'shared_attorney_pending_invoice', OK),
            ('attorney', 'shared_attorney_sent_invoice', OK),
            ('attorney', 'shared_attorney_to_be_paid_invoice', FORBIDDEN),
            ('attorney', 'shared_attorney_paid_invoice', FORBIDDEN),
            # Check that attorney can't access to foreign invoices
            ('attorney', 'other_invoice', NOT_FOUND),

            # Shared attorney and Support users cases

            # Attorney's invoices
            ('support', 'attorney_pending_invoice', OK),
            ('support', 'attorney_sent_invoice', OK),
            ('support', 'attorney_to_be_paid_invoice', FORBIDDEN),
            ('support', 'attorney_paid_invoice', FORBIDDEN),
            # Support's invoices
            ('support', 'support_pending_invoice', OK),
            ('support', 'support_sent_invoice', OK),
            ('support', 'support_to_be_paid_invoice', FORBIDDEN),
            ('support', 'support_paid_invoice', FORBIDDEN),
            # Shared attorney's invoices
            ('support', 'shared_attorney_pending_invoice', OK),
            ('support', 'shared_attorney_sent_invoice', OK),
            ('support', 'shared_attorney_to_be_paid_invoice', FORBIDDEN),
            ('support', 'shared_attorney_paid_invoice', FORBIDDEN),
            # Check that support can't access to foreign invoices
            ('support', 'other_invoice', NOT_FOUND),

            # Attorney's invoices
            ('shared_attorney', 'attorney_pending_invoice', OK),
            ('shared_attorney', 'attorney_sent_invoice', OK),
            ('shared_attorney', 'attorney_to_be_paid_invoice', FORBIDDEN),
            ('shared_attorney', 'attorney_paid_invoice', FORBIDDEN),
            # Support's invoices
            ('shared_attorney', 'support_pending_invoice', OK),
            ('shared_attorney', 'support_sent_invoice', OK),
            ('shared_attorney', 'support_to_be_paid_invoice', FORBIDDEN),
            ('shared_attorney', 'support_paid_invoice', FORBIDDEN),
            # Shared attorney's invoices
            ('shared_attorney', 'shared_attorney_pending_invoice', OK),
            ('shared_attorney', 'shared_attorney_sent_invoice', OK),
            ('shared_attorney', 'shared_attorney_to_be_paid_invoice', FORBIDDEN), # noqa
            ('shared_attorney', 'shared_attorney_paid_invoice', FORBIDDEN),
            # Check that shared_attorney can't access to foreign invoices
            ('shared_attorney', 'other_invoice', NOT_FOUND),
        ),
        indirect=True
    )
    def test_update_invoice(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code: int,
        invoice: models.Invoice,
        matter: models.Matter
    ):
        """Test that attorney, support can update invoices, but clients not."""
        matter.status = models.Matter.STATUS_ACTIVE
        matter.save()
        data = serializers.InvoiceSerializer(instance=invoice).data
        api_client.force_authenticate(user=user)
        response = api_client.put(get_detail_url(invoice), data)
        assert response.status_code == status_code, response.data

    @pytest.mark.parametrize(
        argnames='user, invoice, status_code',
        argvalues=(
            # Client user cases
            # Attorney's invoices
            ('client', 'attorney_pending_invoice', FORBIDDEN),
            ('client', 'attorney_sent_invoice', FORBIDDEN),
            ('client', 'attorney_to_be_paid_invoice', FORBIDDEN),
            ('client', 'attorney_paid_invoice', FORBIDDEN),
            # Support's invoices
            ('client', 'support_pending_invoice', FORBIDDEN),
            ('client', 'support_sent_invoice', FORBIDDEN),
            ('client', 'support_to_be_paid_invoice', FORBIDDEN),
            ('client', 'support_paid_invoice', FORBIDDEN),
            # Shared attorney's invoices
            ('client', 'shared_attorney_pending_invoice', FORBIDDEN),
            ('client', 'shared_attorney_sent_invoice', FORBIDDEN),
            ('client', 'shared_attorney_to_be_paid_invoice', FORBIDDEN),
            ('client', 'shared_attorney_paid_invoice', FORBIDDEN),
            # Check that client can't access to foreign invoices
            ('client', 'other_invoice', FORBIDDEN),

            # Attorney user cases
            # Attorney's invoices
            ('attorney', 'attorney_pending_invoice', NO_CONTENT),
            ('attorney', 'attorney_sent_invoice', NO_CONTENT),
            ('attorney', 'attorney_to_be_paid_invoice', FORBIDDEN),
            ('attorney', 'attorney_paid_invoice', FORBIDDEN),
            # Support's invoices
            ('attorney', 'support_pending_invoice', NO_CONTENT),
            ('attorney', 'support_sent_invoice', NO_CONTENT),
            ('attorney', 'support_to_be_paid_invoice', FORBIDDEN),
            ('attorney', 'support_paid_invoice', FORBIDDEN),
            # Shared attorney's invoices
            ('attorney', 'shared_attorney_pending_invoice', NO_CONTENT),
            ('attorney', 'shared_attorney_sent_invoice', NO_CONTENT),
            ('attorney', 'shared_attorney_to_be_paid_invoice', FORBIDDEN),
            ('attorney', 'shared_attorney_paid_invoice', FORBIDDEN),
            # Check that attorney can't access to foreign invoices
            ('attorney', 'other_invoice', NOT_FOUND),

            # Shared attorney and Support users cases

            # Attorney's invoices
            ('support', 'attorney_pending_invoice', NO_CONTENT),
            ('support', 'attorney_sent_invoice', NO_CONTENT),
            ('support', 'attorney_to_be_paid_invoice', FORBIDDEN),
            ('support', 'attorney_paid_invoice', FORBIDDEN),
            # Support's invoices
            ('support', 'support_pending_invoice', NO_CONTENT),
            ('support', 'support_sent_invoice', NO_CONTENT),
            ('support', 'support_to_be_paid_invoice', FORBIDDEN),
            ('support', 'support_paid_invoice', FORBIDDEN),
            # Shared attorney's invoices
            ('support', 'shared_attorney_pending_invoice', NO_CONTENT),
            ('support', 'shared_attorney_sent_invoice', NO_CONTENT),
            ('support', 'shared_attorney_to_be_paid_invoice', FORBIDDEN),
            ('support', 'shared_attorney_paid_invoice', FORBIDDEN),
            # Check that support can't access to foreign invoices
            ('support', 'other_invoice', NOT_FOUND),

            # Attorney's invoices
            ('shared_attorney', 'attorney_pending_invoice', NO_CONTENT),
            ('shared_attorney', 'attorney_sent_invoice', NO_CONTENT),
            ('shared_attorney', 'attorney_to_be_paid_invoice', FORBIDDEN),
            ('shared_attorney', 'attorney_paid_invoice', FORBIDDEN),
            # Support's invoices
            ('shared_attorney', 'support_pending_invoice', NO_CONTENT),
            ('shared_attorney', 'support_sent_invoice', NO_CONTENT),
            ('shared_attorney', 'support_to_be_paid_invoice', FORBIDDEN),
            ('shared_attorney', 'support_paid_invoice', FORBIDDEN),
            # Shared attorney's invoices
            ('shared_attorney', 'shared_attorney_pending_invoice', NO_CONTENT),
            ('shared_attorney', 'shared_attorney_sent_invoice', NO_CONTENT),
            ('shared_attorney', 'shared_attorney_to_be_paid_invoice', FORBIDDEN), # noqa
            ('shared_attorney', 'shared_attorney_paid_invoice', FORBIDDEN),
            # Check that shared_attorney can't access to foreign invoices
            ('shared_attorney', 'other_invoice', NOT_FOUND),
        ),
        indirect=True
    )
    def test_can_delete_invoice(
        self, api_client: APIClient, user: AppUser, invoice: models.Invoice,
        status_code: int, matter: models.Matter
    ):
        """Test that attorney, support can delete invoices, but clients not."""
        matter.status = models.Matter.STATUS_ACTIVE
        matter.save()
        api_client.force_authenticate(user=user)
        response = api_client.delete(get_detail_url(invoice))
        assert response.status_code == status_code
