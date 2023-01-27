from unittest.mock import MagicMock

import pytest
from quickbooks import objects as qb_objects

from libs.quickbooks import default_quickbooks_client as quickbooks
from libs.quickbooks.exceptions import ObjectNotFound
from libs.quickbooks.services import create_qb_object

from ..models import QBInvoice
from ..services.conversion import (
    _format_date,
    client_to_qb_object,
    invoice_to_qb_object,
    time_billing_attachment_to_qb_object,
)
from ..services.utils import create_or_update_invoice, sync_invoice


@pytest.mark.parametrize(
    argnames='invoice,',
    argvalues=('invoice_no_time_billing', 'invoice_with_time_billing'),
    indirect=True
)
def test_invoice_to_qb_object_no_time_billings(invoice):
    """Test `invoice_to_qb_object` conversion."""
    fake_customer = qb_objects.Customer()
    qb_invoice = invoice_to_qb_object(invoice, fake_customer)

    # check that correct Invoice was created with required TimeBillings count
    assert isinstance(qb_invoice, qb_objects.Invoice)
    # one line is added because of description
    assert len(qb_invoice.Line) == invoice.time_billing.count() + 1


def test_time_billing_attachment_to_qb_object(invoice_with_time_billing):
    """Test `time_billing_attachment_to_qb_object` conversion."""
    time_billing = invoice_with_time_billing.time_billing.first()
    attachment = time_billing.attached_invoice.first()
    qb_obj = time_billing_attachment_to_qb_object(attachment)

    # check that correct SalesItemLine was created
    assert isinstance(qb_obj, qb_objects.SalesItemLine)
    assert qb_obj.LineNum == 0
    assert qb_obj.Amount == time_billing.fees
    assert qb_obj.SalesItemLineDetail.ServiceDate == \
        _format_date(time_billing.date)
    assert qb_obj.Description


def test_client_to_qb_object(client):
    """Test `client_to_qb_object` conversion."""
    qb_obj = client_to_qb_object(client)

    # check that correct Customer was created
    assert isinstance(qb_obj, qb_objects.Customer)
    assert qb_obj.GivenName == client.user.first_name
    assert qb_obj.FamilyName == client.user.last_name
    assert qb_obj.DisplayName == client.display_name
    assert qb_obj.CompanyName == client.organization_name
    assert qb_obj.PrimaryEmailAddr.Address == client.email


def test_sync_invoice(client, invoice_no_time_billing, attorney):
    """Test `sync_invoice` method.

    Check that during this function call new `QBInvoice` object is created with
    correct params.

    """
    qb_invoice = create_qb_object(qb_objects.Invoice, Id=100)
    qb_customer = create_qb_object(qb_objects.Customer, Id=101)
    obj = sync_invoice(
        invoice=invoice_no_time_billing,
        user=attorney.user,
        qb_invoice=qb_invoice,
        qb_customer=qb_customer,
        qb_company_id='Test'
    )

    # check that correct QBInvoice was created
    obj.refresh_from_db()
    assert obj.user == attorney.user
    assert obj.invoice == invoice_no_time_billing
    assert obj.qb_invoice_id == qb_invoice.Id
    assert obj.qb_customer_id == qb_customer.Id

    # check that after the same function call no new QBInvoice created
    obj_2 = sync_invoice(
        invoice=invoice_no_time_billing,
        user=attorney.user,
        qb_invoice=qb_invoice,
        qb_customer=qb_customer,
        qb_company_id='Test'
    )
    assert obj.id == obj_2.id


def test_create_or_update_invoice_no_existing(
    client, invoice_with_time_billing, attorney, mocker
):
    """Test `create_or_update_invoice` method.

    Check that when there is no `existing` QBInvoice yet, object just would be
    `saved` and synchronized in QBInvoice.

    """
    mocker.patch(
        'apps.accounting.services.utils.get_export_record_for_invoice',
        return_value=None
    )
    get_invoice = mocker.patch(
        'libs.quickbooks.clients.QuickBooksTestClient.get_invoice',
    )
    sync_invoice = mocker.patch('apps.accounting.services.utils.sync_invoice')
    create_or_update_invoice(
        invoice_with_time_billing,
        quickbooks().get_customer(1),
        quickbooks()
    )
    # check what methods were called
    get_invoice.assert_not_called()
    sync_invoice.assert_called()


def test_create_or_update_invoice_with_existing(
    client, invoice_with_time_billing, attorney, mocker
):
    """Test `create_or_update_invoice` method.

    Check that when there is `existing` QBInvoice, there would be an extra
    request to resync `invoice` object data.

    """
    mocker.patch(
        'apps.accounting.services.utils.get_export_record_for_invoice',
        return_value=MagicMock()
    )
    get_invoice = mocker.patch(
        'libs.quickbooks.clients.QuickBooksTestClient.get_invoice',
    )
    sync_invoice = mocker.patch('apps.accounting.services.utils.sync_invoice')
    create_or_update_invoice(
        invoice_with_time_billing,
        quickbooks().get_customer(1),
        quickbooks()
    )
    # check what methods were called
    get_invoice.assert_called()
    sync_invoice.assert_called()


def test_create_or_update_invoice_with_existing_not_found(
    client, invoice_with_time_billing, attorney, mocker
):
    """Test `create_or_update_invoice` method.

    Check that when there is `existing` QBInvoice, which is absent in
    QuickBooks there would be an extra request to delete such QBInvoice.

    """
    mocker.patch(
        'apps.accounting.services.utils.get_export_record_for_invoice',
        return_value=QBInvoice(qb_invoice_id=1)
    )
    get_invoice = mocker.patch(
        'libs.quickbooks.clients.QuickBooksTestClient.get_invoice',
        side_effect=ObjectNotFound('No object')
    )
    delete_qb_invoice = mocker.patch('apps.accounting.models.QBInvoice.delete')
    sync_invoice = mocker.patch('apps.accounting.services.utils.sync_invoice')
    create_or_update_invoice(
        invoice_with_time_billing,
        quickbooks().get_customer(1),
        quickbooks()
    )
    # check what methods were called
    get_invoice.assert_called()
    delete_qb_invoice.assert_called()
    sync_invoice.assert_called()
