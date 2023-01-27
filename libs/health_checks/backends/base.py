from abc import ABC

from django.utils.translation import gettext_lazy as _

from health_check.backends import BaseHealthCheckBackend


class AbstractHealthCheckBackend(BaseHealthCheckBackend, ABC):
    """Abstract Health check to add customs methods or override methods."""
    working_status = _('OK')
    _identifier = None
    _description = None

    def pretty_status(self):
        """Make `OK` customizable instead of just `working`."""
        if self.errors:
            return '\n'.join(str(e) for e in self.errors)
        return self.working_status

    def identifier(self):
        """Get health check's identifier."""
        return self._identifier

    @property
    def description(self):
        """Identifier of health check that can be display to user."""
        return self._description
