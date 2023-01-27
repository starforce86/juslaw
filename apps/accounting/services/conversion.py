from datetime import date

from quickbooks import objects as qb_objects

from libs.quickbooks.services import create_qb_object

from apps.business.models import BillingItemAttachment, Invoice
from apps.users.models.clients import Client


def invoice_to_qb_object(
    invoice: Invoice, qb_customer: qb_objects.Customer
) -> qb_objects.Invoice:
    """Shortcut to convert `Invoice` to appropriate QB Invoice object.

    Perform fields mapping to interpret app Invoices to QB Invoices format.
    Currently app Invoice is represented as a simple QB Invoice with few
    `SalesItemLine` objects with Info.

    Arguments:
        invoice (Invoice): app Invoice instance that should be exported to QB
        qb_customer (qb_objects.Customer): QB Customer object, to which invoice
            attached

    """
    qb_obj = create_qb_object(
        qb_class=qb_objects.Invoice,
        CustomerRef=qb_customer.to_ref(),
        BillEmail=qb_customer.PrimaryEmailAddr
    )

    # add common description line for invoice
    description = (
        f'Matter: #{invoice.matter.code} - {invoice.matter.title}\n\n'
        f'Invoice: {invoice.title}\n'
        f'({_format_date(invoice.period_start)} - '
        f'{_format_date(invoice.period_end)})\n\n'
    )
    qb_obj.Line.append(
        create_qb_object(
            qb_class=qb_objects.DescriptionOnlyLine,
            Description=description,
        )
    )

    # prepare invoice description from BillingItems
    attachments = BillingItemAttachment.objects.filter(invoice=invoice) \
        .order_by('time_billing__date')
    for num, attachment in enumerate(attachments, start=1):
        qb_line = time_billing_attachment_to_qb_object(attachment, num)
        qb_obj.Line.append(qb_line)

    return qb_obj


def time_billing_attachment_to_qb_object(
    attachment: BillingItemAttachment, line_num: int = 0
) -> qb_objects.SalesItemLine:
    """Shortcut to convert `BillingItemAttachment` to QB Invoice Line object.

    Arguments:
        attachment (BillingItemAttachment): app TBA instance of some invoice
        line_num (int): line number under which TBA added in QB invoice

    """
    tb = attachment.time_billing
    description = (
        f'Job description: {tb.description}\n'
        f'Time spent: {tb.time_spent}\n'
    )

    return create_qb_object(
        qb_class=qb_objects.SalesItemLine,
        LineNum=line_num,
        Amount=tb.fees,
        Description=description,
        SalesItemLineDetail=create_qb_object(
            qb_class=qb_objects.SalesItemLineDetail,
            ServiceDate=_format_date(tb.date)
        )
    )


def client_to_qb_object(client: Client) -> qb_objects.Customer:
    """Shortcut to convert `Client` to appropriate QB Customer object.

    Arguments:
        client (Client): app Client instance converted to QB Customer

    """
    return create_qb_object(
        qb_class=qb_objects.Customer,
        GivenName=client.user.first_name,
        FamilyName=client.user.last_name,
        DisplayName=client.display_name,
        CompanyName=client.organization_name,
        PrimaryEmailAddr=create_qb_object(
            qb_class=qb_objects.EmailAddress,
            Address=client.email
        ),
    )


def _format_date(obj: date):
    """Shortcut to format date in corresponding for QB date format."""
    return date.strftime(obj, '%Y-%m-%d')
