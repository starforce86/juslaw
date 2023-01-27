from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ...core.admin import BaseAdmin
from ...esign.models import Envelope
from .. import models


@admin.register(models.Lead)
class LeadAdmin(BaseAdmin):
    """Django Admin for Lead model."""
    autocomplete_fields = (
        'attorney',
        'client',
        'post'
    )
    list_display = (
        'id',
        'priority',
        'post',
        'status',
        'created',
        'modified'
    )
    list_display_links = ('id', 'post')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'post',
                'client',
                'attorney',
                'status',
                'priority',
                'chat_channel',
            )
        }),
    )
    search_fields = ('post__title',)
    autocomplete_list_filter = (
        'attorney',
        'client',
        'post',
    )
    list_filter = (
        'priority',
    )
    list_select_related = (
        'post',
        'client',
        'attorney',
    )
    create_only_fields = (
        'post',
        'client',
        'attorney',
        'status'
    )
    readonly_fields = ('chat_channel',)
    ordering = ('created',)
    related_models = (
        models.Matter,
    )


@admin.register(models.Matter)
class MatterAdmin(BaseAdmin):
    """Django Admin for Matter model."""
    list_display = (
        'id',
        'code',
        'title',
        'status',
        'lead',
        'created',
        'modified'
    )
    list_display_links = (
        'id',
        'code',
        'title',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'code',
                'title',
                'description',
            )
        }),
        (_('Related info'), {
            'fields': (
                'client',
                'attorney',
                'lead',
            )
        }),
        (_('Status'), {
            'fields': (
                'status',
                'stage',
                'completed',
            )
        }),
        (_('Rates'), {
            'fields': (
                'fee_type',
                'rate',
            )
        }),
        (_('Location'), {
            'fields': (
                'country',
                'state',
                'city',
            )
        }),
    )
    search_fields = ('code', 'title',)
    autocomplete_fields = (
        'country',
        'state',
        'city',
        'stage',
        'attorney',
        'client',
        'lead',
    )
    autocomplete_list_filter = (
        'lead',
        'client',
        'attorney',
    )
    list_filter = (
        'status',
    )
    list_select_related = (
        'lead__client',
        'lead__client__user',
        'lead__attorney',
        'lead__attorney__user',
    )
    readonly_fields = ('completed',)
    create_only_fields = (
        'post',
        'client',
        'attorney',
        'status',
        'lead',
    )
    ordering = ('created',)
    related_models = (
        models.BillingItem,
        models.Invoice,
        models.Activity,
        models.Note,
        models.VoiceConsent,
        models.MatterSharedWith,
        Envelope
    )
