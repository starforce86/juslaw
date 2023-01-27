import logging

from rest_framework import mixins, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_condition import And, Or

from ....core.api import views
from ....users.api.permissions import (
    IsAttorneyHasActiveSubscription,
    IsClient,
    IsSupportPaidFee,
)
from ... import models, signals
from .. import filters, serializers
from .core import BusinessViewSetMixin

logger = logging.getLogger('django')


class VideoCallViewSet(
    BusinessViewSetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    views.BaseViewSet
):
    """API viewset for `VideoCall` model.

    Provide create, retrieve and list actions.

    """
    queryset = models.VideoCall.objects.all().prefetch_related(
        'participants'
    )
    serializer_class = serializers.VideoCallSerializer
    filterset_class = filters.VideoCallFilter
    default_permissions = [And(
        IsAuthenticated(),
        (Or(
            IsAttorneyHasActiveSubscription(),
            IsClient(),
            IsSupportPaidFee()
        ))
    )]
    permissions_map = {
        'default': default_permissions,
    }
    ordering_fields = (
        'created',
        'modified',
    )

    def create(self, request, *args, **kwargs):
        """Create video call.

        First we check if video call is already created with user and
        participants, if not we create a new video call entry.

        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        # Extract data that would be set after video call creation
        participants = set(serializer.validated_data['participants'])
        participants.add(user.pk)

        video_call = models.VideoCall.objects.get_by_participants(
            participants
        )

        if not video_call:
            video_call = models.VideoCall.objects.create()
            video_call.participants.set(participants)

        signals.new_video_call.send(
            instance=video_call,
            caller=user,
            sender=models.VideoCall,
            user=user
        )

        serializer.instance = video_call
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class BaseAttorneyRelatedViewSet(views.CRUDViewSet):
    """Base CRUD viewset for attorney related data (ChecklistEntry, Stage)."""

    # read is allowed for attorneys or support users
    permission_classes = (BusinessViewSetMixin.attorney_support_permissions,)

    #  CRUD is allowed only for attorneys with active subscriptions
    permissions_map = {
        'create': BusinessViewSetMixin.attorney_permissions,
        'update': BusinessViewSetMixin.attorney_permissions,
        'partial_update': BusinessViewSetMixin.attorney_permissions,
        'destroy': BusinessViewSetMixin.attorney_permissions,
    }

    def get_matter(self, user):
        """Shortcut to get available for user `matter` from query params."""
        matter_id = self.request.query_params.get('matter')
        matter = get_object_or_404(
            models.Matter.objects.all().available_for_user(user),
            id=matter_id
        ) if matter_id else None
        return matter

    def get_queryset(self):
        """Return corresponding instances."""
        qs = super().get_queryset()
        user = self.request.user
        matter = self.get_matter(user) \
            if self.action in ['list', 'retrieve'] else None
        if matter is None:
            referrals = models.Matter.objects.select_related('referral').\
                filter(referral__attorney_id=user.pk)
            ids = list(referrals.values_list('attorney_id', flat=True))
            return qs.filter(attorney_id__in=ids + [user.pk])
        else:
            return qs.filter(attorney_id=matter.attorney_id)


class ChecklistEntryViewSet(BaseAttorneyRelatedViewSet):
    """CRUD api viewset for `ChecklistEntry` model

    For `List`, `Retrieve`:
        - no `matter` query param is set - return only attorney's instances
        - `matter` is set - return matter's attorney instances

    For `Create`, `Update`, `Delete` - return only user attorney's instances

    """
    queryset = models.ChecklistEntry.objects.all()
    serializer_class = serializers.ChecklistEntrySerializer
    filterset_class = filters.ChecklistEntryFilter
    search_fields = (
        'description',
    )
    ordering_fields = (
        'id',
        'description',
        'created',
        'modified',
    )


class StageViewSet(BaseAttorneyRelatedViewSet):
    """CRUD api viewset for `Stage` model

    For `List`, `Retrieve`:
        - no `matter` query param is set - return only attorney's instances
        - `matter` is set - return matter's attorney instances

    For `Create`, `Update`, `Delete` - return only user attorney's instances

    """
    queryset = models.Stage.objects.all()
    serializer_class = serializers.StageSerializer
    filterset_class = filters.StageFilter
    search_fields = (
        'title',
    )
    ordering_fields = (
        'id',
        'title',
        'created',
        'modified',
    )
