from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.core.api.views import CRUDViewSet
from apps.users.api.permissions import IsAttorneyHasActiveSubscription

from ...promotion import models
from . import filters, permissions, serializers


class EventViewSet(CRUDViewSet):
    """CRUD api viewset for Event model."""
    queryset = models.Event.objects.all()
    serializer_class = serializers.EventSerializer
    filterset_class = filters.EventFilter
    event_permissions = (
        IsAuthenticated,
        IsAttorneyHasActiveSubscription,
    )
    permissions_map = {
        'list': (AllowAny,),
        'retrieve': (AllowAny,),
        'create': event_permissions,
        'update': event_permissions + (permissions.IsEventOrganizer,),
        'partial_update': event_permissions + (permissions.IsEventOrganizer,),
        'destroy': event_permissions + (permissions.IsEventOrganizer,),
    }
    search_fields = (
        'title',
        '@attorney__user__first_name',
        '@attorney__user__last_name',
        'attorney__user__email',
    )
    ordering_fields = (
        'id',
        'start',
        'end',
    )
