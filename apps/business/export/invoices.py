from libs.export.resources import PDFResource

from ..models import BillingItem
from ..services import get_invoice_period_str_representation


class InvoiceResource(PDFResource):
    """Resource for Invoice PDF export."""

    template = 'business/export/invoice.html'

    def get_template_context(self):
        """Get all related to Invoice PDF context."""
        context = super().get_template_context()
        attachments = context['object'].attached_time_billing.values(
            'time_billing'
        )
        context.update({
            'matter': self.instance.matter,
            'month_period': get_invoice_period_str_representation(
                self.instance, '%B', 'month'
            ),
            'year_period': get_invoice_period_str_representation(
                self.instance, '%Y', 'year'
            ),
            'date_period': get_invoice_period_str_representation(
                self.instance, '%d %B %Y'
            ),
            'time_billed': self.instance.time_billed,
            'fees_earned': self.instance.fees_earned,
            'billing_item': BillingItem.objects.filter(id__in=attachments)
        })
        return context
