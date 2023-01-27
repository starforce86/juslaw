import logging

from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated

from rest_condition import And, Or

from ....core.api import views
from ....users.api.permissions import (
    IsAttorneyHasActiveSubscription,
    IsClient,
    IsParalegal,
    IsSupportPaidFee,
)
from ... import models
from .. import filters, serializers
from .core import BusinessViewSetMixin

logger = logging.getLogger('django')


class ActivityViewSet(BusinessViewSetMixin, views.ReadOnlyViewSet):
    """Read only api viewset for `Activity` model."""
    queryset = models.Activity.objects.all().select_related(
        'matter',
        'user',
    )
    serializer_class = serializers.ActivitySerializer
    filterset_class = filters.ActivityFilter
    search_fields = (
        'title',
        'matter__title',
        'matter__code',
    )
    ordering_fields = (
        'id',
        'created',
        'modified',
        'title',
        'matter__title',
    )


class VoiceConsentViewSet(
    BusinessViewSetMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    views.ReadOnlyViewSet
):
    """API viewset for `VoiceConsent` model.

    Voice consents are available for reading for all kind of users - attorneys,
    clients, shared attorneys and support. Only clients can create voice
    consents. Only attorneys, shared attorneys and support can remove matter's
    voice consents in available for them matters.

    """
    queryset = models.VoiceConsent.objects.all().prefetch_related('matter')
    serializer_class = serializers.VoiceConsentSerializer
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
        'create': BusinessViewSetMixin.client_permissions,
        'destroy': (BusinessViewSetMixin.attorney_support_permissions,),
    }
    filterset_class = filters.VoiceConsentFilter
    ordering_fields = (
        'created',
        'modified',
    )


class NoteViewSet(BusinessViewSetMixin, views.CRUDViewSet):
    """CRUD api viewset for `Note` model."""
    queryset = models.Note.objects.all().select_related(
        'matter',
        'matter__referral__attorney__user',
        'matter__attorney__user',
        'matter__client__user',
        'client',
        'created_by'
    ).prefetch_related(
        'attachments'
    )
    serializer_class = serializers.NoteSerializer
    serializers_map = {
        'update': serializers.UpdateNoteSerializer,
        'partial_update': serializers.UpdateNoteSerializer,
    }
    # notes can be created, updated and deleted by `client`, `attorney`
    # with active subscription or support who paid fee
    user_permissions = [And(
        IsAuthenticated(),
        (Or(
            IsAttorneyHasActiveSubscription(),
            IsParalegal(),
            IsClient(),
            IsSupportPaidFee()
        ))
    )]
    permissions_map = {
        'create': user_permissions,
        'update': user_permissions,
        'partial_update': user_permissions,
        'destroy': user_permissions,
    }
    filterset_class = filters.NoteFilter
    search_fields = (
        'title',
        'matter__title',
    )
    ordering_fields = (
        'id',
        'title',
        'matter',
        'created',
        'modified',
    )

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        return qs.exclude(
            matter__status=models.Matter.STATUS_REFERRAL,
            matter__referral__attorney__user=user
        )


class MatterSharedWithViewSet(BusinessViewSetMixin, views.ReadOnlyViewSet):
    """Read only api viewset for `MatterSharedWith` model.

    Used by front-end to retrieve info about matter for `new_matter_shared`
    notification.

    """
    queryset = models.MatterSharedWith.objects.all().select_related(
        'matter',
        'user'
    )
    serializer_class = serializers.MatterSharedWithSerializer
    filterset_class = filters.MatterSharedWithFilter
    search_fields = (
        'matter__title',
        'matter__code',
    )
    ordering_fields = (
        'id',
        'created',
        'modified',
        'matter__title',
    )
