from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

__all__ = (
    'QBInvoice',
)


class QBInvoice(BaseModel):
    """Simple model to store exported in QuickBooks invoices.

    It is needed to track whether the invoice was already exported or not.

    """

    user = models.ForeignKey(
        'users.AppUser',
        on_delete=models.CASCADE,
        related_name='qb_invoices',
        verbose_name=_('User'),
        help_text=_('User'),
    )
    invoice = models.ForeignKey(
        'business.Invoice',
        on_delete=models.CASCADE,
        related_name='qb_invoices',
        verbose_name=_('Invoice'),
        help_text=_('Invoice'),
    )
    qb_company_id = models.CharField(
        max_length=20,
        verbose_name=_('QB company ID'),
        help_text=_('Company ID in QuickBooks (realmId)')
    )
    qb_invoice_id = models.IntegerField(
        verbose_name=_('QB Invoice ID'),
        help_text=_('Invoice ID in QuickBooks')
    )
    qb_customer_id = models.IntegerField(
        verbose_name=_('QB Customer ID'),
        help_text=_('Customer ID in QuickBooks')
    )

    class Meta:
        verbose_name = _('QuickBooks Invoice')
        verbose_name_plural = _('QuickBooks Invoices')
        unique_together = (
            'user',
            'invoice',
            'qb_company_id',
            'qb_invoice_id',
            'qb_customer_id'
        )

    def __str__(self):
        return f'{self.user}: {self.invoice}'
