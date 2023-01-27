from rest_framework import mixins
from rest_framework.permissions import AllowAny

from ....core.api.views import BaseViewSet
from ...api import filters, serializers
from ...models import AttorneyUniversity


class AttorneyUniversityViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """Api view to list all universities of attorneys."""
    serializer_class = serializers.AttorneyUniversitySerializer
    base_permission_classes = (AllowAny,)
    queryset = AttorneyUniversity.objects.verified_universities()
    filter_class = filters.AttorneyUniversityFilter
    search_fields = [
        'title',
    ]
