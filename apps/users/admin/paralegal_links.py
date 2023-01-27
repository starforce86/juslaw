from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ...core.admin import BaseAdmin
from .. import models


class ModelWithTitleAdmin(BaseAdmin):
    """Common admin for model with title"""
    list_display = ('id', 'title', 'created')
    search_fields = ('title',)
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
            )
        }),
    )


@admin.register(models.ParalegalUniversity)
class ParalegalUniversityAdmin(ModelWithTitleAdmin):
    """Admin panel for University"""
