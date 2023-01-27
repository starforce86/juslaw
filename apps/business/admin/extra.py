from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ...core.admin import BaseAdmin, ReadOnlyAdmin
from .. import models


@admin.register(models.Stage)
class StageAdmin(BaseAdmin):
    """Django Admin for `Stage` model."""
    list_display = (
        'id',
        'title',
        'attorney',
    )
    list_display_links = ('id', 'title')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'attorney',
                'title',
            )
        }),
    )
    search_fields = ('title',)
    create_only_fields = (
        'attorney',
    )
    autocomplete_fields = (
        'attorney',
    )
    autocomplete_list_filter = (
        'attorney',
    )
    ordering = ('created', 'modified')
    related_models = (
        models.Matter,
    )


@admin.register(models.ChecklistEntry)
class ChecklistEntryAdmin(BaseAdmin):
    """Django Admin for `ChecklistEntry` model."""
    list_display = (
        'id',
        'attorney',
        'description',
    )
    list_display_links = ('id', 'attorney')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'attorney',
                'description',
            )
        }),
    )
    search_fields = ('description',)
    create_only_fields = ('attorney',)
    autocomplete_fields = ('attorney',)
    autocomplete_list_filter = (
        'attorney',
    )
    ordering = ('created', 'modified')


@admin.register(models.Referral)
class ReferralAdmin(ReadOnlyAdmin, BaseAdmin):
    """Django Admin for `Referral` model."""
    list_display = (
        'id',
        'attorney',
        'message'
    )
    list_display_links = ('id', 'message')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'attorney',
                'message',
            )
        }),
    )
    search_fields = ('message',)
    create_only_fields = (
        'attorney',
    )
    autocomplete_fields = (
        'attorney',
    )
    autocomplete_list_filter = (
        'attorney',
    )
    related_models = (
        models.Matter,
    )


@admin.register(models.PaymentMethods)
class PaymentMethodsAdmin(BaseAdmin):
    """Django Admin for `PaymentMethods` model."""
    list_display = (
        'id',
        'title',
    )
    list_display_links = ('id', 'title')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
            )
        }),
    )
    search_fields = ('title',)
    ordering = ('title',)
