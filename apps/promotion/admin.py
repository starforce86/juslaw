from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..core.admin import BaseAdmin
from . import models


@admin.register(models.Event)
class EventAdmin(BaseAdmin):
    """Event representation for admin."""
    list_display = (
        'id',
        'title',
        'attorney',
        'timezone',
        'is_all_day',
        'start',
        'end',
    )
    autocomplete_fields = ('attorney', )
    list_display_links = ('id', 'title')
    search_fields = ('title',)
    readonly_fields = (
        'duration',
    )
    create_only_fields = (
        'attorney',
        'timezone',
    )
    list_filter = (
        'is_all_day',
    )
    autocomplete_list_filter = (
        'attorney',
    )
    list_select_related = (
        'attorney',
        'attorney__user',
    )
    ordering = ('start', 'end')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
                'description',
                'attorney',
                'timezone',
            )
        }),
        (_('Time'), {
            'fields': (
                'start',
                'end',
                'duration',
                'is_all_day',
            )
        }),
        (_('Location'), {
            'fields': (
                'location',
            )
        }),
    )
