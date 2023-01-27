import typing
from collections import namedtuple
from datetime import date as dt_date

import arrow

from ...finance.models import Payment
from ...finance.services import create_payment
from ...users.models import AppUser
from .. import models
from ..notifications import InvoiceEmailNotification

InvoicePeriod = namedtuple('InvoicePeriod', ['period_start', 'period_end'])

__all__ = (
    'get_invoice_period_str_representation',
    'get_invoice_period_ranges',
    'get_invoice_for_matter',
    'send_invoice_to_recipients',
    'prepare_invoice_for_payment',
    'get_or_create_invoice_payment',
)


def get_invoice_period_str_representation(
    invoice: models.Invoice, date_format: str, equality_attr: str = None
) -> str:
    """Shortcut to get string representation of invoice period.

    Method prepares invoice period string representation in a `date_format`.
    If there is planned a check for some `start` and `end` attribute equality
    -> don't repeat value (there will be returned `Oct` instead of `Oct - Oct`)

    Args:
        invoice (Invoice) - invoice instance
        date_format (datetime) - returned format for a separate date
        equality_attr (str) - name of attr that should be checked by equality

    Returns:
        (str) - invoice period string in a desired format

    """
    start, end = invoice.period_start, invoice.period_end
    if equality_attr:
        start_attr = getattr(start, equality_attr, None)
        end_attr = getattr(end, equality_attr, None)
        # return only one date in case of similar values
        if start_attr == end_attr:
            return start.strftime(date_format)
    # return period in case of different values
    return f'{start.strftime(date_format)} - {end.strftime(date_format)}'


def get_invoice_period_ranges(
    date: typing.Union[dt_date, arrow.Arrow]
) -> InvoicePeriod:
    """Shortcut to get invoice period ranges from defined `date`.

    Method gets `date` and calculates fist and last days of a date's month and
    returns it in a `InvoicePeriod` format.

    Args:
        date (date) - date to which invoice ranges should be calculated

    Returns:
        (InvoicePeriod) - calculated values for invoice `period_start` and
            `period_end`

    """
    if isinstance(date, dt_date):
        date = arrow.get(date)
    period_start, period_end = date.span('month')
    return InvoicePeriod(
        period_start=period_start.datetime,
        period_end=period_end.datetime
    )


def get_invoice_for_matter(
    matter: models.Matter, period_start: dt_date, period_end: dt_date
) -> models.Invoice:
    """Shortcut to get or create invoice for a matter for a desired period.

    Method checks if there exists and invoice for the desired period and uses
    it if it exists, otherwise it creates a new invoice.

    Args:
        matter (Matter) - matter for which invoice should be generated
        period_start (date) - date of invoice start period
        period_end (date) - date of invoice end period

    Returns:
        (Invoice) - created or get invoice for a matter

    """
    # check if invoice for a desired period for this matter already exists
    invoice = matter.invoices.filter(
        period_start=period_start, period_end=period_end
    ).first()
    if invoice:
        return invoice

    # create new invoice if it doesn't exist
    invoice = models.Invoice.objects.create(
        matter=matter,
        created_by_id=matter.attorney_id,
        period_start=period_start,
        period_end=period_end,
        title=f'{matter.title} Invoice',
    )
    return invoice


def send_invoice_to_recipients(
    invoice: models.Invoice,
    recipient_list: typing.Sequence[str],
    note: str = None,
    user: AppUser = None
) -> bool:
    """Send generated pdf report file from invoice to recipients."""
    from ..signals import invoice_is_sent

    email_context = {
        'note': note
    }
    email = InvoiceEmailNotification(
        recipient_list=recipient_list,
        invoice=invoice,
        **email_context
    )
    send_status = email.send()

    # send a signal that invoice was sent
    if send_status:
        invoice_is_sent.send(
            sender=invoice._meta.model,
            instance=invoice,
            user=user
        )

    return send_status


def prepare_invoice_for_payment(invoice: models.Invoice):
    """Prepare invoice to be paid through Stripe Connect.

    Before payment toward invoice we need to strip other
    invoices from time billing attached to input invoice.

    """
    # Get all time billings pks from invoice
    time_billings_pks = invoice.time_billing.values_list('pk', flat=True)
    # Delete attachments to other time billings
    models.BillingItemAttachment.objects.exclude(invoice=invoice).filter(
        time_billing_id__in=time_billings_pks
    ).delete()


def get_or_create_invoice_payment(invoice: models.Invoice) -> Payment:
    """Get or create payment for Invoice."""
    if invoice.payment:
        payment = invoice.payment
    else:
        payment = create_payment(
            amount=invoice.fees_earned,
            description=f'Payment for Invoice #{invoice.pk}-{invoice.title}',
            payer_id=invoice.matter.client_id,
            recipient_id=invoice.matter.attorney_id,
        )
    payment.start_payment_process()
    payment.save()
    return payment


def create_invoice_item(invoice: models.Invoice, stripe_invoice_item):
    if stripe_invoice_item is not None:
        invoice.activities.add(
            models.InvoiceActivity.objects.create(
                activity=(f"An invoice item for ${invoice.total_amount}USD "
                          f"was created for {invoice.client.user.email}")
            )
        )
        invoice.logs.add(
            models.links.InvoiceLog.objects.create(
                status='200 OK',
                method='POST',
                log='/v1/invoiceitems'
            )
        )
    else:
        invoice.logs.add(
            models.links.InvoiceLog.objects.create(
                status='400 BAD REQUEST',
                method='POST',
                log='/v1/invoiceitems'
            )
        )
    invoice.save()


def create_draft_invoice(invoice: models.Invoice, stripe_invoice):
    if stripe_invoice is not None:
        invoice.activities.add(
            models.InvoiceActivity.objects.create(
                activity="A draft invoice was created"
            )
        )
        invoice.activities.add(
            models.InvoiceActivity.objects.create(
                activity=(f"{invoice.client.user.email}'s "
                          "invoice item was added to an invoice")
            )
        )
        invoice.logs.add(
            models.links.InvoiceLog.objects.create(
                status='200 OK',
                method='POST',
                log='/v1/invoices'
            )
        )
    else:
        invoice.logs.add(
            models.links.InvoiceLog.objects.create(
                status='400 BAD REQUEST',
                method='POST',
                log='/v1/invoices'
            )
        )
    invoice.save()


def send_invoice(invoice: models.Invoice, stripe_invoice):
    if stripe_invoice is None:
        invoice.logs.add(
            models.InvoiceLog.objects.create(
                status='400 BAD REQUEST',
                method='POST',
                log=f'/v1/invoices/{invoice.invoice_id}/send'
            )
        )
    else:
        invoice.logs.add(
            models.InvoiceLog.objects.create(
                status='200 OK',
                method='POST',
                log=f'/v1/invoices/{invoice.invoice_id}/send'
            )
        )
        invoice.activities.add(
            models.InvoiceActivity.objects.create(
                activity=(f"A draft invoice for ${invoice.total_amount}USD "
                          f"to {invoice.client.user.email} was finalized")
            )
        )
        invoice.activities.add(
            models.InvoiceActivity.objects.create(
                activity=(f"{invoice.client.user.email}'s "
                          f"for ${invoice.total_amount}USD invoice was sent")
            )
        )
    invoice.save()


def pay_invoice(invoice: models.Invoice, stripe_invoice):
    if stripe_invoice is None:
        invoice.logs.add(
            models.InvoiceLog.objects.create(
                status='400 BAD REQUEST',
                method='POST',
                log=f'/v1/invoices/{invoice.invoice_id}/pay'
            )
        )
    else:
        invoice.logs.add(
            models.InvoiceLog.objects.create(
                status='200 OK',
                method='POST',
                log=f'/v1/invoices/{invoice.invoice_id}/pay'
            )
        )
        invoice.activities.add(
            models.InvoiceActivity.objects.create(
                activity=(f"A invoice for ${invoice.total_amount}USD "
                          f"to {invoice.client.user.email} was paid")
            )
        )
    invoice.save()


def clone_invoice(obj, attrs={}):

    clone = obj._meta.model.objects.get(pk=obj.pk)
    clone.pk = None
    for key, value in attrs.items():
        setattr(clone, key, value)
    clone.save()
    fields = clone._meta.get_fields()
    for field in fields:
        if not field.auto_created and field.many_to_many:
            for row in getattr(obj, field.name).all():
                getattr(clone, field.name).add(row)
        if field.auto_created and field.is_relation:
            if field.many_to_many:
                pass
            else:
                attrs = {
                    field.remote_field.name: clone
                }
                children = field.related_model.objects.filter(
                    **{field.remote_field.name: obj}
                )
                for child in children:
                    clone_invoice(child, attrs)
    return clone
