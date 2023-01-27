from django import forms
from django.core.paginator import Page
from django.utils.encoding import force_str

from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.request import override_method


class ReducedBrowsableAPIRenderer(BrowsableAPIRenderer):
    """BrowsableAPIRenderer that hides some info.

    This renderer works and looks similar to default DRF API renderer,
    but do not show forms for editing data (this forms contain all possible
    values), filters and docstrings.

    It is helpful for performance issues tracking with debug toolbar, cause
    it avoids not optimal uploading of selectors in DRF `filter` and
    `create/update` forms.

    """

    def get_rendered_html_form(self, data, view, method, request):
        """Never show any forms for editing.

        We have a lot of custom serializers fields, which does not support
        well form inputs, so we do not show any html forms
        """
        return

    def get_filter_form(self, data, view, request):
        """Hide filter form

        Here we disable filter form for all DRF API methods for performance
        tracking.

        Adding filters is a problem when there is a filter by some instance and
        DRF selects corresponding choices with separate queries, which is not
        optimal.

        """
        return

    def show_form_for_method(self, view, method, request, obj):
        """Hide/display form for raw input

        Here we disable raw content form for bulk updates
        """
        bulk_update_actions = [
            'bulk_update',
            'partial_bulk_update'
        ]
        res = super().show_form_for_method(view, method, request, obj)

        if getattr(view, 'action', None) in bulk_update_actions:
            return False

        return res

    def get_raw_data_form(self, data, view, method, request):
        """Override method to remove readonly fields from raw form

        Code is almost copy-pasted from DRF sources
        """
        # See issue #2089 for refactoring this.
        serializer = getattr(data, 'serializer', None)
        if serializer and not getattr(serializer, 'many', False):
            instance = getattr(serializer, 'instance', None)
            if isinstance(instance, Page):
                instance = None
        else:
            instance = None

        with override_method(view, request, method) as fake_request:
            # Check permissions
            if not self.show_form_for_method(
                    view, method, fake_request, instance):
                return

            # If possible, serialize the initial content for the generic form
            default_parser = view.parser_classes[0]
            renderer_class = getattr(default_parser, 'renderer_class', None)
            if hasattr(view, 'get_serializer') and renderer_class:
                # View has a serializer defined and parser class has a
                # corresponding renderer that can be used to render the data.

                # try to display user's input data
                if request.method in ['POST', 'PUT', 'PATCH']:
                    serializer_data = request.data
                else:
                    # if it GET request - show empty data with defaults
                    if method in ('PUT', 'PATCH'):
                        serializer = view.get_serializer(instance=instance)
                    else:
                        serializer = view.get_serializer()

                    # changes here
                    # remove not editable fields from data
                    serializer_data = serializer.data
                    for field_name, field in serializer.fields.items():
                        if field.read_only:
                            serializer_data.pop(field_name, None)

                # Render the raw data content
                renderer = renderer_class()
                accepted = self.accepted_media_type
                context = self.renderer_context.copy()
                context['indent'] = 4
                content = force_str(
                    renderer.render(serializer_data, accepted, context)
                )

            else:
                content = None

            # Generate a generic form that includes a content type field,
            # and a content field.
            media_types = [parser.media_type for parser in view.parser_classes]
            choices = [(media_type, media_type) for media_type in media_types]
            initial = media_types[0]

            class GenericContentForm(forms.Form):
                _content_type = forms.ChoiceField(
                    label='Media type',
                    choices=choices,
                    initial=initial,
                    widget=forms.Select(
                        attrs={'data-override': 'content-type'}
                    )
                )
                _content = forms.CharField(
                    label='Content',
                    widget=forms.Textarea(
                        attrs={'data-override': 'content'}
                    ),
                    initial=content
                )

            return GenericContentForm()

    def get_description(self, view, status_code):
        """Do not show any description for view.

        By default, DRF renders view's docstring, but our views contains
        descriptions for developers, so we hide this
        """
        return ''
