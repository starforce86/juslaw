from rest_framework.response import Response
from rest_framework.views import APIView

from libs.swagger import get_current_swagger_spec_version


class SwaggerSpecVersionView(APIView):
    """View for swagger version retrieval."""

    def get(self, request):
        """Report the version of the swagger specification that the API."""
        return Response({
            'version': get_current_swagger_spec_version()
        })
