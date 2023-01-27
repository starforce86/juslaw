import json
from functools import partial

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.forms.models import modelform_factory
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

__all__ = (
    'ForbidDeleteAdd',
    'PrettyPrintMixin',
    'FkAdminLink',
    'AllFieldsReadOnly',
    'ForbidChangeMixin',
)


class ForbidChangeMixin(object):
    """Mixin forbid change permission for django admin."""

    def has_change_permission(self, request, obj=None):
        return False


class ForbidDeleteAdd(object):
    """Added forbid permission for objects.

    The mixin redefining two methods of ``ModelAdmin`` and both these methods
    will return false, do not allow adding and deleting objects.

    """

    def delete_model(self, request, obj):
        """Do nothing on delete."""
        return

    def get_actions(self, request):
        """Disable "delete_selected" action."""
        actions = super().get_actions(request)

        if 'delete_selected' in actions:
            del actions['delete_selected']

        return actions

    def has_add_permission(self, request, obj=None):
        """Check that user has add permission."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Check that user has delete permission."""
        return False


class FkAdminLink(object):
    """Mixin to add link to object's admin.

    This class could be inherited by any other class.

    Example:
        class Book(models.Model):
            author = models.ForeignKey('user')
            content = models.TextField()


        class BookAdmin(models.ModelAdmin, FkAdminLink):
            readonly_fields = ('_author',)

            def _author(self, obj):
                return self._admin_url(obj.author)

            # or with title

            def _author(self, obj):
                return self._admin_url(
                    obj.author,
                    obj.author.last_name + obj.author.first_name[0]
                )

    """

    def _get_admin_url(self, obj):
        content_type = ContentType.objects.get_for_model(
            obj, for_concrete_model=False,
        )
        admin_url_str = (
            f'admin:{content_type.app_label}_{content_type.model}_change'
        )
        return reverse(admin_url_str, args=[obj.pk])

    def _admin_url(self, obj, title=None):
        admin_url = self._get_admin_url(obj)
        return format_html(
            "<a href='{0}' target='_blank'>{1}</a>",
            admin_url, title or str(obj))


class AllFieldsReadOnly(object):
    """Make all field read only.

    Simple mixin if you want to make all fields readonly without specifying
    fields attribute.

    """

    def get_readonly_fields(self, request, obj=None):
        """Return fields with readonly access."""
        if self.fields:
            return self.fields

        # took this django sources
        if self.exclude is None:
            exclude = []
        else:
            exclude = list(self.exclude)

        if (self.exclude is None and hasattr(self.form, '_meta') and
                self.form._meta.exclude):
            # Take the custom ModelForm's Meta.exclude into account only if the
            # ModelAdmin doesn't define its own.
            exclude.extend(self.form._meta.exclude)

        # if exclude is an empty list we pass None to be consistent with the
        # default on modelform_factory
        exclude = exclude or None

        defaults = {
            'form': self.form,
            'fields': forms.ALL_FIELDS,
            'exclude': exclude,
            'formfield_callback': partial(
                self.formfield_for_dbfield,
                request=request
            )
        }
        form = modelform_factory(self.model, **defaults)

        return list(form.base_fields)


class PrettyPrintMixin(object):
    """Mixin for pretty displaying readonly python objects in admin.

    May be used for pretty displaying complex objects, like dicts, lists.

    Provide one method - `pretty_print`
    """

    def pretty_print(self, obj):
        """Return pretty jsoned representation of ``obj``."""
        return mark_safe(json.dumps(obj, indent=4)
                         .replace(' ', '&nbsp').replace('\n', '<br>'))
