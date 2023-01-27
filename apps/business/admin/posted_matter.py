from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ...core.admin import BaseAdmin
from .. import models


@admin.register(models.PostedMatter)
class PostedMatterAdmin(BaseAdmin):
    """Django Admin for PostedMatter model."""
    list_display = (
        'id',
        'title',
        'description',
        'status',
        'created',
        'modified'
    )
    list_display_links = (
        'id',
        'title',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
                'description',
            )
        }),
        (_('Related info'), {
            'fields': (
                'client',
                'practice_area',
            )
        }),
        (_('Status'), {
            'fields': (
                'status',
                'status_modified',
            )
        }),
        (_('Budget'), {
            'fields': (
                'budget_min',
                'budget_max',
                'budget_type',
                'budget_detail',
            )
        }),
    )
    search_fields = ('title',)
    autocomplete_fields = (
        'client',
    )
    autocomplete_list_filter = (
        'client',
    )
    list_filter = (
        'status',
    )
    create_only_fields = (
        'budget_min',
        'budget_max',
        'budget_type',
        'budget_detail',
        'status',
    )
    ordering = ('created',)


@admin.register(models.Proposal)
class ProposalAdmin(BaseAdmin):
    """Django Admin for PostedMatter model."""
    list_display = (
        'id',
        'attorney',
        'post',
        'description',
        'status',
        'created',
        'modified'
    )
    list_display_links = (
        'id',
        'description',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'description',
            )
        }),
        (_('Related info'), {
            'fields': (
                'attorney',
                'post',
            )
        }),
        (_('Status'), {
            'fields': (
                'status',
                'status_modified',
            )
        }),
        (_('Rate'), {
            'fields': (
                'rate',
                'rate_type',
                'rate_detail',
                'currency',
            )
        }),
    )
    search_fields = ('title',)
    autocomplete_fields = (
        'attorney',
    )
    autocomplete_list_filter = (
        'attorney',
    )
    list_filter = (
        'status',
    )
    create_only_fields = (
        'status',
    )
    ordering = ('created',)
