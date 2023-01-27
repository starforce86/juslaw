from django.apps import AppConfig


class AccountingAppDefaultConfig(AppConfig):
    """Default configuration for `Accounting` app."""

    name = 'apps.accounting'
    verbose_name = 'Accounting'

    def ready(self):
        """Enable schema definitions."""
        from .api import schema  # noqa
