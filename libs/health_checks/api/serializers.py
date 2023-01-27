from rest_framework import serializers

from ..apps import HEALTH_CHECKS


class HealthCheckQuery(serializers.Serializer):
    """Serializer for validation query params for health check endpoint."""
    checks = serializers.MultipleChoiceField(
        required=False,
        choices=HEALTH_CHECKS,
    )


class HealthCheckResult(serializers.Serializer):
    """Serializer for one health check result"""
    status = serializers.CharField()
    description = serializers.CharField()


class HealthCheckResults(serializers.Serializer):
    """Serializer for full health check results."""

    def get_fields(self):
        """Set up fields for all checkers."""
        return {
            health_check: HealthCheckResult(label=health_check, required=False)
            for health_check in HEALTH_CHECKS
        }
