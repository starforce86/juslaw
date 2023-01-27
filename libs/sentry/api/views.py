from sentry_sdk import Scope, configure_scope


class SentryMixin:
    """Mixin that adds sentry support to view."""

    def handle_exception(self, exc):
        """Add wrapper to exception with sentry scope."""
        with configure_scope() as scope:
            self.set_up_scope(scope)
            return super().handle_exception(exc)

    def set_up_scope(self, scope: Scope):
        """Add additional data to sentry error report."""
        scope.set_tag('type', 'api')
        scope.set_tag('api_name', self.basename)
        scope.set_tag('api_action', self.action)
