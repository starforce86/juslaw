import datetime
import logging
import traceback
from datetime import timedelta
from decimal import Decimal

from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import stripe
from dirtyfields import DirtyFieldsMixin
from django_fsm import FSMField, transition

from libs.django_fcm.exceptions import TransitionFailedException

from ...core.models import BaseModel
from ...finance.models.payments.payments import AbstractPaidObject
from .extra import Attachment, PaymentMethods
from .querysets import BillingItemQuerySet, InvoiceQuerySet

__all__ = (
    'BillingItem',
    'Invoice',
    'BillingItemAttachment',
)

from ...users.models import Client

logger = logging.getLogger('django')


class BillingItem(DirtyFieldsMixin, BaseModel):
    """BillingItem model.

    This model represents amount of time spent by attorney on corresponding
    matter (kind of time logging).

    Attributes:
        matter (Matter): matter in which the work is billed
        created_by (AppUser): appuser which created time billing
        invoices (BillingItemAttachment): invoices to which this billed work is
            connected
        description (text): described work in human words
        date (date): date in which billed work was done
        time_spent (duration): amount of time spent by attorney to the work
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time
        billing_type (text choices): Represents billing type, it can be
            expense: If billing is for an expanse
            time: If billing is for logged time
        is_billable (bool): if time entry is billable
        client (Client): client who is gonna be charged
        hourly_rate (Decimal): hourly rate which is charged if its a time entry
        quantity (int): Quantity if its an expense entry
        rate (decimal): Unit price if its expense entry
        attachment (FileField): Attachment required if billing type is expense
    """
    attachments = models.ManyToManyField(
        Attachment,
        verbose_name=_('File'),
        help_text=_("Billing item attachments"),
    )
    is_billable = models.BooleanField(
        default=False,
        verbose_name=_('Is billable entry'),
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='billed_item',
        verbose_name=_('Client'),
        null=True
    )
    matter = models.ForeignKey(
        'Matter',
        verbose_name=_('Matter'),
        related_name='billing_item',
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        'users.AppUser',
        editable=False,
        verbose_name=_('Created by'),
        help_text=_('AppUser created time billing'),
        related_name='billing_item',
        on_delete=models.PROTECT,
    )
    billed_by = models.ForeignKey(
        'users.AppUser',
        verbose_name=_('Billed by'),
        related_name='billed_item',
        on_delete=models.PROTECT,
        null=True
    )
    invoices = models.ManyToManyField(
        'Invoice',
        verbose_name=_('Invoices'),
        through='BillingItemAttachment',
        related_name='time_billing',
    )
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Full description of made work')
    )
    time_spent = models.DurationField(
        verbose_name=_('Time Spent'),
        help_text=_('Amount of time that attorney spent on this work'),
        validators=[
            validators.MinValueValidator(datetime.timedelta(minutes=15)),
            validators.MaxValueValidator(datetime.timedelta(hours=24)),
        ],
        null=True,
        blank=True
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Hourly rate'),
        help_text=_('Hourly rate for which time entry is added'),
        default=0
    )
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Rate'),
        help_text=_('Unit rate for which expense entry is added'),
        null=True,
        default=None
    )
    quantity = models.PositiveIntegerField(
        verbose_name=_('Quantity'),
        help_text=_('Quantity of the item for which expense entry is added'),
        null=True,
        default=None
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Total amount'),
        help_text=_('Total amount for which expense entry is added'),
        default=0
    )
    currency = models.ForeignKey(
        'users.Currencies',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Currency")
    )
    date = models.DateField(
        verbose_name=_('Date'),
        help_text=_('Date in which billed work was made')
    )
    BILLING_TYPE_EXPENSE = 'expense'
    BILLING_TYPE_TIME = 'time'
    BILLING_TYPE_FLAT_FEE = 'flat_fee'
    BILLING_TYPES = (
        (BILLING_TYPE_EXPENSE, _('Expense')),
        (BILLING_TYPE_TIME, _('Time')),
        (BILLING_TYPE_FLAT_FEE, _('Flat fee'))
    )

    billing_type = models.CharField(
        choices=BILLING_TYPES,
        max_length=10,
        default=BILLING_TYPE_TIME,
        verbose_name=_("Billing Type")
    )

    objects = BillingItemQuerySet.as_manager()

    class Meta:
        verbose_name = _('Billing Item')
        verbose_name_plural = _('Billing Item')

    def __str__(self):
        return f'{self.description[:5]} @ {self.matter}'

    @property
    def available_for_editing(self) -> bool:
        """Check if time billing related to read only invoice."""
        if hasattr(self, '_available_for_editing'):
            return self._available_for_editing
        if not self.invoices.all().exists():
            # This for case when tb is new and it's not attached to any invoice
            return True
        return self.invoices.available_for_editing().exists()

    @property
    def fee(self) -> float:
        """Calculate fee based on time and expense"""
        amount = 0
        if self.billing_type == BillingItem.BILLING_TYPE_TIME:
            if self.time_spent is not None:
                amount = float(self.hourly_rate) * \
                    self.time_spent.total_seconds() / 3600
        else:
            amount = float(self.total_amount)
        return amount

    @classmethod
    def attorney_billing_items(cls, matters):
        return cls.objects.filter(matter__in=matters)

    @property
    def is_billed(self) -> bool:
        """Check if billing item attached to invoice."""
        return self.billing_items_invoices.count() > 0


class TimeEntry(BaseModel):
    start_time = models.DateTimeField(
        verbose_name=_('Start time')
    )
    end_time = models.DateTimeField(
        null=True,
        verbose_name=_('End time')
    )
    billing_item = models.ForeignKey(
        BillingItem,
        on_delete=models.CASCADE,
        verbose_name=_('Billing Item'),
        related_name='time_entries',
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        'users.AppUser',
        editable=False,
        verbose_name=_('Created by'),
        help_text=_('AppUser created time billing'),
        related_name='time_entries',
        on_delete=models.PROTECT,
        null=True
    )

    @classmethod
    def calculate_elapsed_time(cls, created_by):
        time_entries = cls.objects.filter(
            created_by=created_by,
            billing_item__isnull=True
        )
        is_running = False
        time_elapsed = timedelta()
        for time_entry in time_entries:
            start = time_entry.start_time
            end = time_entry.end_time or timezone.now()
            time_elapsed += end - start
            if time_entry.end_time is None:
                is_running = True
        return time_elapsed, is_running

    @classmethod
    def elapsed_time_without_microseconds(cls, created_by):
        elapsed_time_exact, is_running = cls.calculate_elapsed_time(created_by)
        return str(elapsed_time_exact).split('.')[0], is_running

    @classmethod
    def get_running_time_entry(cls, created_by):
        return cls.objects.filter(
            created_by=created_by,
            billing_item__isnull=True,
            end_time__isnull=True
        ).order_by(
            '-created'
        ).first()


class BillingItemAttachment(BaseModel):
    """Many-to-many relation between billing items and invoices

    Attributes:
        billing_items (BillingItem): Foreign key for billing item
        invoice (Invoice): Foreign key for invoice

    """
    time_billing = models.ForeignKey(
        'BillingItem',
        verbose_name=_('Time Billing'),
        on_delete=models.CASCADE,
        related_name='attached_invoice',
    )
    invoice = models.ForeignKey(
        'Invoice',
        verbose_name=_('Invoice'),
        on_delete=models.CASCADE,
        related_name='attached_time_billing'
    )

    class Meta:
        verbose_name = _('Attached Time Billing')
        verbose_name_plural = _('Attached Time Billings')

    @property
    def available_for_editing(self) -> bool:
        """Check if time billing attachment related to read only invoice."""
        return self.invoice.available_for_editing

    @property
    def is_paid(self) -> bool:
        """Check if time billing attachment related to paid invoice."""
        return self.invoice.is_paid

    def __str__(self):
        return (
            f'#{self.id}. Time billing #{self.time_billing_id} attached to '
            f'Invoice #{self.invoice_id}-{self.invoice.title}'
        )

    def clean_invoice(self):
        """Clean BillingItemAttachment instances."""
        if self.time_billing.matter_id != self.invoice.matter_id:
            raise ValidationError(_(
                "Invoice's `matter` doesn't match BillingItem `matter`"
            ))

        if not self.invoice.matter.is_hourly_rated:
            raise ValidationError(_(
                "It's not allowed to attach time billings with invoices for "
                "not `hourly` rated matters"
            ))

        if (
            self.invoice.period_start > self.time_billing.date or
            self.invoice.period_end < self.time_billing.date
        ):
            raise ValidationError(_(
                "Time Billing date is not from selected invoice time period."
            ))


class Invoice(AbstractPaidObject, DirtyFieldsMixin, BaseModel):
    """Invoice model

    This model represents amount of money which Client should pay for
    Attorney's services in a defined dates period.

    Invoices are only sent to matters which have `hourly` rate type.

    Attributes:
        number (str): invoice number from stripe
        invoice_id (str): invoice id from stripe
        client (Client): is the client to which invoice is calculated
        matter (Matter): is the matter to which invoice is calculated
        billing_items (BillingItems): are the billing_items in invoice
        period_start (date): start date from which invoice is calculated
        period_end (date): end date till which invoice is calculated
        title (str): the name/title of invoice (for example, for what services
        it is and etc)
        status (str): current status of invoice, it can be:
            pending, sent, payment_in_progress, payment_failed, and paid.
            Pending -> Set when invoice is created. Can't be seen by client.
            Sent -> Set when invoice is sent to client or when payment is
            canceled.
            Payment in progress -> Set when client starting paying for
            invoice(when front-end requests payment_intent) or resumes payment
            process.
            Payment failed -> Set when payment for invoice failed. Failed
                invoice's payment can still be paid and marked as paid
            Paid -> Set payment for invoice was successful.
            Statuses when attorney can edit invoice and related to it
            time billings -> Pending and Sent
            Statuses when attorney can't edit invoice and related to it
            time billings -> Payment in progress or Paid
            You can find out whenever you can edit or not by checking out
            `available_for_editing` property
        note (str): attorney can leave note on invoice sending
        payment_method (PaymentMethods): Payment method for executing payment
        payment (Payment): Link to payment object, all payments towards invoice
        created_by (AppUser): User who created invoice, in celery task it's set
            to matter's owner
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time
        due_date (date): Represents the due date for the invoice
        due_days (int): Number of due days
        email (email): email of client
        finalized (datetime): timestamp when instance was finalized
        activities (InvoiceActivity): activities of invoice
        logs (InvoiceLog): logs of invoice
    """
    number = models.CharField(
        verbose_name=_('Invoice Number'),
        max_length=15,
        null=True
    )
    invoice_id = models.CharField(
        verbose_name=_('Invoice ID'),
        max_length=30,
        null=True
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True,
        blank=True
    )
    matter = models.ForeignKey(
        'Matter',
        related_name='invoices',
        on_delete=models.SET_NULL,
        null=True,
    )
    billing_items = models.ManyToManyField(
        'BillingItem',
        verbose_name=_('billing_items'),
        related_name='billing_items_invoices'
    )
    period_start = models.DateField(
        verbose_name=_('Period start'),
        help_text=_(
            'Start date from which invoice money amount is calculated'
        ),
    )
    period_end = models.DateField(
        verbose_name=_('Period end'),
        help_text=_('End date till which invoice money amount is calculated')
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Title which describes current invoice')
    )

    INVOICE_STATUS_OVERDUE = 'overdue'
    INVOICE_STATUS_OPEN = 'open'
    INVOICE_STATUS_PAID = 'paid'
    INVOICE_STATUS_VOIDED = 'voided'
    INVOICE_STATUS_DRAFT = 'draft'

    AVAILABLE_FOR_EDITING_STATUSES = (
        AbstractPaidObject.PAYMENT_STATUS_NOT_STARTED,
    )
    FORBID_EDITING = (
        AbstractPaidObject.PAYMENT_STATUS_IN_PROGRESS,
        AbstractPaidObject.PAYMENT_STATUS_FAILED,
        AbstractPaidObject.PAYMENT_STATUS_PAID,
    )

    INVOICE_STATUSES = (
        (INVOICE_STATUS_OVERDUE, _('Overdue')),
        (INVOICE_STATUS_OPEN, _('Open')),
        (INVOICE_STATUS_PAID, _('Paid')),
        (INVOICE_STATUS_VOIDED, _('Voided')),
        (INVOICE_STATUS_DRAFT, _('Draft')),
    )

    status = FSMField(
        max_length=30,
        choices=INVOICE_STATUSES,
        default=INVOICE_STATUS_DRAFT,
        verbose_name=_('Status'),
        help_text=_('Status of invoice')
    )

    payment_method = models.ManyToManyField(
        PaymentMethods,
        verbose_name=_('Payment methods'),
        related_name='invoices'
    )

    note = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Note'),
        help_text=_('A note left by attorney')
    )

    created_by = models.ForeignKey(
        to='users.AppUser',
        editable=False,
        verbose_name=_('Created by'),
        help_text=_('AppUser that created invoice'),
        related_name='invoices',
        on_delete=models.PROTECT,
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text=_(
            "The date on which payment for this invoice is due."
        ),
        verbose_name='Due Date'
    )
    due_days = models.IntegerField(
        default=0,
        help_text=_(
            "The days on which payment for this invoice is due."
        ),
        verbose_name='Due days'
    )
    email = models.EmailField(
        verbose_name=_('Invoice Email'),
        null=True,
    )
    finalized = models.DateTimeField(
        verbose_name=_('Finalized Date'),
        null=True,
        blank=True
    )

    activities = models.ManyToManyField(
        'InvoiceActivity',
        verbose_name=_('activities'),
        related_name='invoices',
    )

    logs = models.ManyToManyField(
        'InvoiceLog',
        verbose_name=_('logs'),
        related_name='invoices',
    )

    # tax
    tax_rate = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        verbose_name=_('Tax rate'),
        help_text=_('Tax rate'),
        null=True,
        default=None
    )

    objects = InvoiceQuerySet.as_manager()

    class Meta:
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')

    def __str__(self):
        return self.title

    @property
    def total_amount(self) -> Decimal:
        amount = 0
        for item in self.billing_items.all():
            amount += float(item.fee)
        return amount

    @property
    def time_billed(self) -> timedelta:
        """Returns sum of jobs spent times."""
        time_billed = timedelta()
        for obj in self.billing_items.all():
            if obj.time_spent:
                time_billed += obj.time_spent
        return time_billed

    @property
    def fees_earned(self) -> float:
        """Returns sum of jobs fees."""
        fees = sum([obj.fee for obj in self.billing_items.all()])
        return fees

    @property
    def can_be_paid(self) -> bool:
        """Check if it's possible to pay for invoice."""
        deposit_account = self.matter.attorney.deposit_account
        return bool(
            self.fees_earned > 0 and
            deposit_account and
            deposit_account.is_verified and
            self.status == self.INVOICE_STATUS_OPEN
        )

    @property
    def available_for_editing(self) -> bool:
        """Is invoice can be edited."""
        return self.payment_status in self.AVAILABLE_FOR_EDITING_STATUSES

    def can_send(self, user) -> bool:
        """Return ``True`` if ``user`` can send invoice.

        Invoice can be sent only by invoice's original `attorney`
        or users with which the matter was shared. Exception is statuses
        related to payments and if invoice has no time billings. Invoice can be
        sent only if it's payment status is in 'not_started'.

        """
        if not user:
            return False

        if self.payment_status != self.PAYMENT_STATUS_NOT_STARTED:
            raise ValidationError(dict(
                payment_status='Invoice is being paid or is already paid'
            ))

        if not self.time_billing.exists():
            raise ValidationError(dict(
                fees_earned="Invoice doesn't have any time billings"
            ))

        matter = self.matter
        return user.pk == matter.attorney_id or matter.is_shared_for_user(
            user
        )

    def can_pay(self, user) -> bool:
        """Return ``True`` if ``user`` can pay for invoice.

        Invoice can be paid only by client. Also invoice can be paid if fees is
        greater than zero (Stripe won't allow us to create PaymentIntent with
        amount equal zero). This can't be used on 'pending' or 'sent'
        transitions, since it's handled by fcm sources params. Also for payment
        we need to invoice's matter's attorney to have account in Stripe
        Connect.

        """
        if not super().can_pay(user):
            return False
        return user.pk == self.matter.client_id and self.can_be_paid

    @transition(
        field=status,
        source=INVOICE_STATUS_DRAFT,
        target=INVOICE_STATUS_OPEN,
        permission=can_send,
    )
    def send(self, user=None):
        """Update invoice status to `open`.

        Update invoice status to `open` and send email with invoice to stated
        client's emails.

        """
        from .. import services
        try:
            invoice = stripe.Invoice.send_invoice(
                self.invoice_id
            )
            services.send_invoice(invoice=self, stripe_invoice=invoice)
            self.finalized = timezone.now()
            self.save()
        except Exception as error:
            logger.error(
                f'Error invoice #{self.pk} PDF sending: {error}\n'
                'Traceback:\n'
                f'{traceback.format_exc()}'
            )
            raise TransitionFailedException('Can not send invoice')

    @transition(
        field=status,
        source=[INVOICE_STATUS_OPEN, INVOICE_STATUS_OVERDUE],
        target=INVOICE_STATUS_PAID,
    )
    def pay(self):
        from .. import services
        try:
            invoice = stripe.Invoice.pay(self.invoice_id)
            services.pay_invoice(invoice=self, stripe_invoice=invoice)
        except Exception as error:
            logger.error(
                f'Error invoice #{self.pk} Paid: {error}\n'
                'Traceback:\n'
                f'{traceback.format_exc()}'
            )
            raise TransitionFailedException('Can not pay invoice')

    def _get_or_create_payment(self):
        """Set up payment."""
        from ..services import get_or_create_invoice_payment
        return get_or_create_invoice_payment(invoice=self)

    def _post_start_payment_process_hook(self):
        """Clean up other invoices."""
        from ..services import prepare_invoice_for_payment
        prepare_invoice_for_payment(invoice=self)

    def _post_fail_payment_hook(self):
        """Notify user about failed payment."""
        from .. import notifications
        notifications.InvoicePaymentFailedNotification(paid_object=self).send()

    def _post_cancel_payment_hook(self):
        """Notify user about canceled payment."""
        from .. import notifications
        notifications.InvoicePaymentCanceledNotification(
            paid_object=self
        ).send()

    def _post_finalize_payment_hook(self):
        """Notify client and attorney about succeeded payment."""
        from .. import notifications
        for recipient in [self.matter.client, self.matter.attorney]:
            notifications.InvoicePaymentSucceededNotification(
                paid_object=self,
                recipient=recipient.user
            ).send()

    # def clean_matter(self):
    #     """Invoices can be created for matters with `hourly` rate type."""
    #     if not self.matter.is_hourly_rated:
    #         raise ValidationError(_(
    #             "Forbidden to add invoices to not `hourly` rated matters"
    #         ))

    @classmethod
    def client_upcoming_invoices(cls, client):
        return cls.objects.filter(
            matter__in=client.matters.all()
        ).exclude(
            payment_status='paid'
        )
