from typing import Union

from rest_framework import permissions

from ..models import BillingItem, Invoice

__all__ = (
    'CanEditOrDeleteInvoiceOrBillingItem',
)


class CanEditOrDeleteInvoiceOrBillingItem(permissions.BasePermission):
    """Check if invoice or time billing can be edited or deleted."""

    def has_object_permission(
        self, request, view, obj: Union[Invoice, BillingItem]
    ) -> bool:
        """Forbid operation if object is not available for editing."""
        return obj.available_for_editing
