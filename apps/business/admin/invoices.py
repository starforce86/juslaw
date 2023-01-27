import typing

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ...accounting.models import QBInvoice
from ...core.admin import BaseAdmin, ReadOnlyAdmin, ReadOnlyMixin
from .. import models


class ForbidPaidEditDeleteMixin:
    """Mixin that forbids editing or deletion if object is paid."""
    def has_change_permission(
        self,
        request,
        obj: typing.Union[
            models.BillingItemAttachment,
            models.BillingItem,
            models.Invoice,
        ] = None
    ) -> bool:
        """Forbid change if obj is paid."""
        if not obj:
            return super().has_change_permission(request, obj)
        return obj.available_for_editing

    def has_delete_permission(
        self,
        request,
        obj: typing.Union[
            models.BillingItemAttachment,
            models.BillingItem,
            models.Invoice,
        ] = None,
    ) -> bool:
        """Forbid delete if obj is paid."""
        if not obj:
            return super().has_delete_permission(request, obj)
        return obj.available_for_editing


@admin.register(models.BillingItemAttachment)
class BillingItemAttachmentAdmin(ReadOnlyAdmin):
    """Django Admin for BillingItemAttachment model."""
    list_display = ('id', 'invoice', 'time_billing')
    list_display_links = ('id',)
    autocomplete_list_filter = (
        'invoice',
        'time_billing',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'invoice',
                'time_billing',
            )
        }),
    )
    search_fields = ('invoice__title', 'time_billing__description')
    ordering = ('created',)
    autocomplete_fields = ('invoice', 'time_billing')


class BillingItemAttachmentInline(
    ReadOnlyMixin, admin.TabularInline
):
    """Inlines list of time billings Attachments."""
    autocomplete_fields = ('time_billing', 'invoice')
    model = models.BillingItemAttachment
    extra = 0
    show_change_link = True
    verbose_name = _('Time Billing Attachment')
    verbose_name_plural = _('Time Billing Attachments')

    def get_queryset(self, request):
        return super().get_queryset(request=request).select_related(
            'invoice',
            'time_billing',
            'time_billing__matter',
        )


@admin.register(models.BillingItem)
class BillingItemAdmin(ReadOnlyMixin, BaseAdmin):
    """Django Admin for BillingItem model."""
    list_display = (
        'id',
        'matter',
        'time_spent',
        'date',
        'created',
        'modified'
    )
    list_display_links = ('id', 'matter')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'matter',
                'created_by',
                'description',
                'date',
                'time_spent',
            )
        }),
    )
    search_fields = ('matter__title',)
    ordering = ('created',)
    readonly_fields = (
        'created_by',
    )
    create_only_fields = (
        'matter',
        'created_by',
    )
    inlines = (
        BillingItemAttachmentInline,
    )
    autocomplete_fields = (
        'matter',
        'created_by'
    )
    autocomplete_list_filter = (
        'matter',
        'created_by',
    )
    related_models = (
        models.BillingItemAttachment,
    )

    def get_queryset(self, request):
        """Add `_available_for_editing` annotation."""
        return super().get_queryset(request=request)\
            .with_available_for_editing()


@admin.register(models.Invoice)
class InvoiceAdmin(ForbidPaidEditDeleteMixin, BaseAdmin):
    """Django Admin for Invoice model."""
    autocomplete_fields = (
        'matter',
        'created_by',
    )
    list_display = (
        'id',
        'matter',
        'created_by',
        'period_start',
        'period_end',
        'status',
        'title',
        'created',
        'modified',
    )
    list_display_links = ('id', 'title')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'number',
                'invoice_id',
                'matter',
                'created_by',
                'period_start',
                'period_end',
                'status',
                'title',
                'note',
                'fees_earned',
                '_payment',
            )
        }),
    )
    readonly_fields = (
        'number',
        'invoice_id',
        'fees_earned',
        'created_by',
        '_payment',
        'status',
    )
    create_only_fields = (
        'matter',
        'created_by',
    )
    search_fields = ('title', )
    autocomplete_list_filter = (
        'matter',
        'created_by',
    )
    list_filter = (
        'status',
        'payment_status',
    )
    ordering = ('created',)
    inlines = (
        BillingItemAttachmentInline,
    )
    related_models = (
        models.BillingItemAttachment,
        QBInvoice,
    )

    def _payment(self, obj: models.Invoice):
        """Return HTML link to `payment`."""
        return self._admin_url(obj.payment)
