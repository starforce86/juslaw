import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ....core.api import views
from ....users.api.permissions import IsAttorneyHasActiveSubscription
from ... import export
from .. import serializers

logger = logging.getLogger('django')


class StatisticsViewSet(views.BaseViewSet):
    """View set for viewing business app statistics."""
    base_filter_backends = None
    pagination_class = None

    permission_classes = (
        IsAuthenticated,
        IsAttorneyHasActiveSubscription,
    )

    @action(detail=False, methods=['GET'])
    def export(self, request, *args, **kwargs):
        """Export business app statistics as Excel file.

        Return:
            response(HttpResponse) - response with attachment

        """
        serializer = serializers.BusinessStatsQueryParamsSerializer(
            data=request.query_params
        )
        serializer.is_valid(raise_exception=True)
        resource = export.AttorneyPeriodBusinessResource(
            instance=request.user,
            **serializer.data
        )
        try:
            data = resource.export()
            response = resource.get_export_file_response(data=data)
            return response
        except Exception as e:
            logger.error(f'Error excel export: {e}')
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
