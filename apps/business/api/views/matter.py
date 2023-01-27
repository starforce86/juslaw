import logging

from django.db.models.query import Prefetch

from rest_framework import response, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404

from django_fsm import TransitionNotAllowed

from libs.django_fcm.api.utils import transition_method

from ....core.api import views
from ....users.api.serializers import ParticipantsSerializer
from ....users.models import AppUser
from ... import models, services
from ...signals import new_matter_referred
from ...signals.extra import new_referral_accepted, new_referral_declined
from .. import filters, serializers
from ..serializers.matter import MatterDocumentSerializer
from .core import BusinessViewSetMixin

logger = logging.getLogger('django')


class LeadViewSet(BusinessViewSetMixin, views.CRUDViewSet):
    """CRUD api viewset for Lead model
    """
    permissions_map = {
        'update': BusinessViewSetMixin.attorney_permissions,
        'partial_update': BusinessViewSetMixin.attorney_permissions,
        'destroy': BusinessViewSetMixin.attorney_permissions,
    }
    queryset = models.Lead.objects.all().select_related(
        'client',
        'client__user',
        'client__state',
        'attorney',
        'attorney__user'
    ).prefetch_related(
        'attorney__user__specialities'
    )
    serializer_class = serializers.LeadSerializer
    serializers_map = {
        'update': serializers.UpdateLeadSerializer,
        'partial_update': serializers.UpdateLeadSerializer,
    }
    filterset_class = filters.LeadFilter
    search_fields = (
        'topic__title',
        '@client__user__first_name',
        '@client__user__last_name',
        'client__user__email',
        'client__organization_name',
        '@attorney__user__first_name',
        '@attorney__user__last_name',
        'attorney__user__email',
    )
    ordering_fields = (
        'id',
        'created',
        'modified',
        'topic__title',
        ('client__first_name', 'client__user__first_name'),
        ('client__last_name', 'client__user__last_name'),
        ('client__email', 'client__user__email'),
        'client__organization_name',
        'attorney__user__first_name',
        'attorney__user__last_name',
        'attorney__user__email',
    )


class MatterViewSet(BusinessViewSetMixin, views.CRUDViewSet):
    """CRUD api viewset for Matter model.

    Fields that are `read only` when matter is not `pending`:
        * `city`
        * `state`
        * `country`
        * `rate`
        * `rate_type`
        * `title`
        * `description`
        * `code`

    """
    # removed with_totals()
    queryset = models.Matter.objects.all().select_related(
        'client',
        'client__user',
        'client__country',
        'client__state',
        'client__city',
        'attorney',
        'attorney__user',
        'speciality',
        'currency',
        'country',
        'state',
        'city',
        'stage',
        'fee_type',
    ).prefetch_related(
        # custom prefetch for `initial` Envelopes only for performance reasons
        # latest envelopes should go first
        # Prefetch(
        #     'envelopes',
        #     queryset=Envelope.objects.filter(type=Envelope.TYPE_INITIAL)
        #     .order_by('-id')
        #     .prefetch_related('documents')
        # ),
        Prefetch(
            'activities',
            queryset=models.Activity.objects.order_by('-created')
        ),
        'shared_with',
        # add this prefetch because of `user_type` field
        'shared_with__attorney',
        'shared_with__paralegal',
        'shared_with__support',
        'shared_with__client',
        'billing_item',
        'billing_item__billing_items_invoices',
        'documents',
        'folders',
        'posts',
        'posts__participants',
        'invoices',
        'invoices__billing_items',
    )
    serializer_class = serializers.MatterSerializer
    transition_result_serializer_class = serializers.MatterSerializer
    serializers_map = {
        'retrieve': serializers.MatterDetailSerializer,
        'update': serializers.UpdateMatterSerializer,
        'partial_update': serializers.UpdateMatterSerializer,
        'share_with': serializers.ShareMatterSerializer,
        # If transition requires data, set it to proper serializer.
        'send_referral': serializers.ReferralSerializer,
        'accept_referral': None,
        'close': None,
        'open': None
    }
    permissions_map = {
        # only attorneys can create new matters
        'create': BusinessViewSetMixin.attorney_permissions,
        'update': (BusinessViewSetMixin.attorney_support_permissions,),
        'share_with': (BusinessViewSetMixin.attorney_support_permissions,),
        # attorney and paralegal can modify matters
        'partial_update': (BusinessViewSetMixin.support_permissions,),
        'close': (BusinessViewSetMixin.support_permissions,),
        'open': (BusinessViewSetMixin.support_permissions,),
        # statuses transitions permissions
        'send_referral': (BusinessViewSetMixin.attorney_support_permissions,),
        'accept_referral': (BusinessViewSetMixin.attorney_support_permissions,)
    }
    filterset_class = filters.MatterFilter
    search_fields = (
        'code',
        'title',
        '@client__user__first_name',
        '@client__user__last_name',
        'client__user__email',
        'client__organization_name',
        '@attorney__user__first_name',
        '@attorney__user__last_name',
        'attorney__user__email',
    )
    ordering_fields = (
        'id',
        'title',
        'created',
        'modified',
        'client__user__first_name',
        'attorney__user__first_name',
        'start_date',
    )

    def get_queryset(self):
        """Annotate qs with `_is_shared` flag for performance reasons."""
        qs = super().get_queryset().with_is_shared_for_user(self.request.user)
        return qs

    def create(self, request, *args, **kwargs):
        request_data = request.data
        """Handle in case client is invite uuid, replace key `client`
        with `invite` if value for key `client` is invite uuid"""
        if request_data.get('invite'):
            if 'client' in request_data.keys():
                del request_data['client']
        else:
            if request_data.get('client') and \
                    not str(request_data['client']).isdigit():
                request_data['invite'] = request_data['client']
                del request_data['client']

        serializer = serializers.MatterSerializer(
            data=request_data, context=super().get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        headers = self.get_success_headers(data)
        matter = serializer.save()
        attachments = request.data.get('attachment', [])
        for attachment in attachments:
            attachment_serializer = MatterDocumentSerializer(
                data={
                    'file': attachment,
                    'owner': request.user.id,
                    'created_by': request.user.id,
                    'matter': matter.id
                }
            )
            attachment_serializer.is_valid(raise_exception=True)
            attachment_serializer.save()
        matter.save()
        serializer = serializers.MatterSerializer(
            instance=matter
        )

        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    # signature of methods doesn't matter because they are overridden
    # in decorators

    @action(detail=True, methods=['POST'])
    @transition_method('open')
    def open(self, *args, **kwargs):
        """Update matter status to `Open`."""

    @action(detail=True, methods=['POST'])
    @transition_method('close')
    def close(self, *args, **kwargs):
        """Update matter status to `Close`."""

    @action(detail=True, methods=['POST'], url_path='share')
    def share_with(self, request, *args, **kwargs):
        """Share (`refer`) matter with another app users.

        This method allows to share matter with another app users, so they
        could help original matter attorney to manage it.

        """
        matter = get_object_or_404(self.get_queryset(), **kwargs)

        if (matter.status in [models.Matter.STATUS_CLOSE]):
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": "It's not allowed to share matters "
                                "in `pending` or `draft` statuses"}
            )
        serializer = self.get_serializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # this method may add new users and remove existing if they were
        # not passed depending on `user_type`
        services.share_matter(
            request.user, matter, **serializer.validated_data
        )
        matter.refresh_from_db()
        return response.Response(
            data=serializers.MatterSerializer(matter).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['POST'], url_path='send_referral')
    def send_referral(self, request, *args, **kwargs):
        """Send referral request to another attorney
        """
        matter = get_object_or_404(self.get_queryset(), **kwargs)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            if matter.attorney.user != request.user:
                return response.Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": "Can not allow send referral"}
                )
            data = serializer.validated_data
            referral = models.Referral.objects.create(**data)
            matter.referral = referral
            matter.send_referral()
            matter.save()
            new_matter_referred.send(
                sender=models.Matter,
                instance=matter,
                notification_sender=self.request.user,
                user=self.request.user
            )
            return response.Response(
                data=serializers.MatterSerializer(
                    matter, context={'request': request}
                ).data,
                status=status.HTTP_200_OK
            )
        except TransitionNotAllowed as e:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": str(e)}
            )

    @action(detail=True, methods=['POST'], url_path='accept_referral')
    def accept_referral(self, request, *args, **kwargs):
        """Accept referral request from another attorney
        """
        try:
            matter = get_object_or_404(self.get_queryset(), **kwargs)
            new_referral_accepted.send(
                sender=models.Matter,
                instance=matter,
                notification_sender=self.request.user,
                user=self.request.user
            )
            matter.delete_referral()
            matter.accept_referral()
            matter.save()
            return response.Response(
                data=serializers.MatterSerializer(matter).data,
                status=status.HTTP_200_OK
            )
        except TransitionNotAllowed:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['POST'], url_path='ignore_referral')
    def ignore_referral(self, request, *args, **kwargs):
        """Ignore referral request from another attorney
        """
        try:
            matter = get_object_or_404(self.get_queryset(), **kwargs)
            new_referral_declined.send(
                sender=models.Matter,
                instance=matter,
                notification_sender=self.request.user,
                user=self.request.user
            )
            # TODO referral object gets deleted move to matter model
            matter.ignore_referral()
            matter.save()
            return response.Response(
                data=serializers.MatterSerializer(matter).data,
                status=status.HTTP_200_OK
            )
        except TransitionNotAllowed:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['GET'])
    def participants(self, request, *args, **kwargs):
        """Return available participants"""
        try:
            matter = get_object_or_404(self.get_queryset(), **kwargs)
            shared_with = matter.shared_with.all()
            if request.user.is_client:
                principal = AppUser.objects.filter(
                    pk=matter.attorney.user.pk
                )
                participants = shared_with | principal
            else:
                client = AppUser.objects.filter(
                    pk=matter.client.user.pk
                )
                participants = shared_with | client
            participants = participants.distinct()
            page = self.paginate_queryset(participants)
            if page is not None:
                serializer = ParticipantsSerializer(
                    page, context={"request": request}, many=True
                )
                return self.get_paginated_response(serializer.data)
            serializer = ParticipantsSerializer(
                participants, context={"request": request}, many=True
            )
            return response.Response(
                status=status.HTTP_200_OK,
                data=serializer.data
            )
        except Exception:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['PUT'])
    def leave_matter(self, request, *args, **kwargs):
        """Leave matter which is shared with"""
        try:
            matter = get_object_or_404(self.get_queryset(), **kwargs)
            matter.shared_with.remove(request.user.pk)
            return response.Response(
                status=status.HTTP_200_OK,
                data={'success': True}
            )
        except Exception:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'success': False}
            )


class OpportunityViewSet(BusinessViewSetMixin, views.CRUDViewSet):
    """View set for opportunity model."""
    permissions_map = {
        'update': BusinessViewSetMixin.attorney_permissions,
        'partial_update': BusinessViewSetMixin.attorney_permissions,
        'destroy': BusinessViewSetMixin.attorney_permissions,
    }
    queryset = models.Opportunity.objects.all().select_related(
        'client',
        'client__user',
        'client__state',
        'attorney',
        'attorney__user',
        'paralegal',
        'paralegal__user'
    ).prefetch_related(
        'attorney__user__specialities',
        'paralegal__user__specialities'
    )
    serializer_class = serializers.OpportunitySerializer
    filterset_class = filters.OpportunityFilter
    search_fields = (
        '@client__user__first_name',
        '@client__user__last_name',
        'client__user__email',
        'client__organization_name',
        '@attorney__user__first_name',
        '@attorney__user__last_name',
        'attorney__user__email',
        '@paralegal__user__first_name',
        '@paralegal__user__last_name',
        'paralegal__user__email',
    )
    ordering_fields = (
        'id',
        'created',
        'modified',
        'client__user__first_name',
        'client__user__last_name',
        'client__user__email',
        'client__organization_name',
        'attorney__user__first_name',
        'attorney__user__last_name',
        'attorney__user__email',
    )
