from django.apps import AppConfig


class FinanceAppDefaultConfig(AppConfig):
    """Default configuration for Finance app."""

    name = 'apps.finance'
    verbose_name = 'Finance'

    def ready(self):
        """Enable signals and schema definitions."""
        from . import webhooks  # noqa
        from .api import schema  # noqa
