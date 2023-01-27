from django.apps import AppConfig


class UsersAppDefaultConfig(AppConfig):
    """Default configuration for Users app."""

    name = 'apps.users'
    verbose_name = 'Users'

    def ready(self):
        """Enable signals and schema definitions."""
        from . import signals  # noqa
        from .api import schema  # noqa
