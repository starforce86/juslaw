from rest_framework.response import Response
from rest_framework.views import APIView

from ..utils import run_checks
from . import serializers


class HealthCheckView(APIView):
    """View for checking out health of app."""

    def get(self, request):
        """Perform health checks and get results."""
        serializer = serializers.HealthCheckQuery(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        plugins = run_checks(**serializer.validated_data)
        data = {
            plugin.identifier(): dict(
                status=plugin.pretty_status(),
                description=plugin.description,
            )
            for plugin in plugins
        }
        result_serializers = serializers.HealthCheckResults(data)
        return Response(
            data=result_serializers.data
        )
