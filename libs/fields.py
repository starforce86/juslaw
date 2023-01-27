import typing

from django.core import validators
from django.core.exceptions import ValidationError
from django.forms import fields
from django.utils.translation import gettext_lazy as _


class URLTemplateValidator(validators.URLValidator):
    """Validator that checks it url template is valid or not.

    Usage:
        For example you need to save a url template that has parameters
        like id and starts and looks like this:
            https://example.com/stuff?id={id}&starts={starts}
        Then all you need to do is pass list of templates keys on __init__.
        Like this: URLTemplateValidator('id', 'starts')

    """

    def __init__(self, *keys, **kwargs):
        """Init validator and set template context."""
        super().__init__(**kwargs)
        self.context = {key: None for key in keys}

    def __call__(self, value):
        """Check that template have needed context."""
        super().__call__(value)

        # Check that template have all needed keys
        for key in self.context.keys():
            if f'{key}' not in value:
                raise ValidationError(_('Incorrect template'))

        # Check that formatting works as intended
        try:
            value.format(**self.context)
        except (KeyError, IndexError):
            raise ValidationError(_('Incorrect template'))


class URLTemplateField(fields.URLField):
    """URL field that accepts url templates."""

    def __init__(self, keys: typing.Sequence[str], **kwargs):
        """Set keys for URLTemplateValidator validator."""
        self.default_validators = [URLTemplateValidator(*keys)]
        super().__init__(**kwargs)
