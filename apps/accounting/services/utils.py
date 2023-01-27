from quickbooks import objects as qb_objects

from libs.quickbooks import exceptions
from libs.quickbooks.clients import QuickBooksClient

from apps.business.models import Invoice
from apps.users.models import AppUser
from apps.users.models.clients import Client

from ..models import QBInvoice
from .conversion import client_to_qb_object, invoice_to_qb_object


def sync_invoice(
    invoice: Invoice,
    qb_invoice: qb_objects.Invoice,
    qb_customer: qb_objects.Customer,
    qb_company_id: str,
    user: AppUser
):
    """Sync QB created/updated Invoice to `QBInvoice`.

    Store info that `invoice` was already exported by user to some company.

    Arguments:
        invoice (Invoice): app Invoice instance that was exported to QB
        qb_invoice (qb_objects.Invoice): QB Invoice with updated info
        qb_customer (qb_objects.Customer): QB Customer with updated info
        qb_company_id (str): company ID (realmId) to which invoice was exported
        user (AppUser): user initiated invoices export

    """

    saved_invoice = get_export_record_for_invoice(
        invoice, qb_customer, qb_company_id, user
    )
    if saved_invoice:
        return saved_invoice

    return QBInvoice.objects.create(
        user=user,
        invoice=invoice,
        qb_company_id=qb_company_id,
        qb_invoice_id=qb_invoice.Id,
        qb_customer_id=qb_customer.Id,
    )


def get_export_record_for_invoice(
    invoice: Invoice,
    qb_customer: qb_objects.Customer,
    qb_company_id: str,
    user: AppUser
):
    """Shortcut to check whether `invoice` was already exported.

    Check whether invoice was already exported by this user to the same QB
    company with the same QB customer

    Arguments:
        invoice (Invoice): app Invoice instance that was exported to QB
        qb_customer (qb_objects.Customer): QB Customer with updated info
        qb_company_id (str): company ID (realmId) to which invoice was exported
        user (AppUser): user initiated invoices export

    """
    return invoice.qb_invoices.filter(
        user=user, qb_company_id=qb_company_id, qb_customer_id=qb_customer.Id
    ).first()


def create_customer(
    client: Client, qb_api_client: QuickBooksClient
) -> qb_objects.Customer:
    """Create QB Customer from app Client.

    Arguments:
        client (Client): app client that should be created
        qb_api_client (QuickBooksClient): client to work with QuickBooks API

    """
    qb_client = client_to_qb_object(client)
    try:
        return qb_api_client.save_object(qb_client)
    except exceptions.DuplicatedObjectError:
        raise exceptions.DuplicatedObjectError('The client already exist')


def create_or_update_invoice(
    invoice: Invoice,
    qb_customer: qb_objects.Customer,
    qb_api_client: QuickBooksClient
) -> qb_objects.Invoice:
    """Create QB Customer from app Client.

    Arguments:
        invoice (Invoice): app invoice that should be created or updated
        qb_customer (qb_objects.Customer): QB Customer object
        qb_api_client (QuickBooksClient): client to work with QuickBooks API

    """
    # prepare simple `invoice` template in QB format
    invoice_template = invoice_to_qb_object(invoice, qb_customer)

    # if invoice already exported get its QB `Id` and `SyncToken` for update
    already_exported = get_export_record_for_invoice(
        invoice, qb_customer, qb_api_client.realm_id, qb_api_client.user
    )
    if already_exported:
        # if exported QBInvoice really exists in QuickBooks, make its resync to
        # get actual `SyncToken`
        try:
            exported_qb_invoice = qb_api_client.get_invoice(
                already_exported.qb_invoice_id
            )
            invoice_template.Id = exported_qb_invoice.Id
            invoice_template.SyncToken = exported_qb_invoice.SyncToken
        # otherwise if exported QBInvoice doesn't exist in QuickBooks - remove
        # it from QBInvoice model
        except exceptions.ObjectNotFound:
            already_exported.delete()

    # perform real create/update request in QuickBooks API
    qb_invoice = qb_api_client.save_object(invoice_template)

    # remember created/updated invoice in QBInvoice
    sync_invoice(
        invoice=invoice,
        qb_invoice=qb_invoice,
        qb_customer=qb_customer,
        qb_company_id=str(qb_api_client.realm_id),
        user=qb_api_client.user
    )

    return qb_invoice
