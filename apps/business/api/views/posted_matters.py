from django.db.models import Q
from django.db.models.query import Prefetch
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_fsm import TransitionNotAllowed

from libs.django_fcm.api.exceptions import WrongTransitionException

from apps.business.api import filters
from apps.business.api.serializers.posted_matters import (
    PostedMattersByPracticeAreaSerializer,
    PostedMatterSerializer,
    ProposalSerializer,
)
from apps.business.models import PostedMatter, Proposal
from apps.business.signals import (
    post_inactivated,
    post_reactivated,
    proposal_accepted,
    proposal_withdrawn,
)
from apps.core.api.views import CRUDViewSet
from apps.forums.models import ForumPracticeAreas


class PostedMatterViewSet(CRUDViewSet):
    """
        View set for Posted Matter view
        provide basic CRUD operations.
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = PostedMatterSerializer
    queryset = PostedMatter.objects.all().select_related(
        'practice_area',
        'client__user',
        'currency',
        'client',
    ).prefetch_related(
        'proposals',
        'proposals__post',
        'proposals__attorney',
        'proposals__attorney__user',
        'proposals__currency'
    )
    filterset_class = filters.PostedMatterFilter
    search_fields = ('title', 'description')
    ordering_fields = (
        'created',
        'modified',
        'status_modified'
    )

    def get_queryset(self):
        qs = super().get_queryset()
        qp = self.request.query_params
        attorney_id = qp.get('attorney', None)
        proposal_id = qp.get('proposal', None)
        if proposal_id:
            return qs.filter(proposals__in=[proposal_id])
        if attorney_id:
            return qs.filter(
                Q(
                    proposals__attorney__in=[attorney_id],
                    status=PostedMatter.STATUS_INACTIVE
                ) | Q(status=PostedMatter.STATUS_ACTIVE)
            ).distinct()
        return qs

    @action(methods=['get'], detail=False)
    def practice_area_stats(self, request, *args, **kwargs):
        """View for posted matter stats for per practice area"""

        practice_area_qs = ForumPracticeAreas.objects.all().prefetch_related(
            Prefetch(
                'posted_matter',
                queryset=PostedMatter.objects.filter(
                    status=PostedMatter.STATUS_ACTIVE
                ).order_by('-created')
            ),
            'posted_matter__currency',
            'posted_matter__client',
            'posted_matter__practice_area',
            'posted_matter__proposals',
            'posted_matter__proposals__attorney',
            'posted_matter__proposals__attorney__user',
            'posted_matter__proposals__currency',
        )
        search_text = request.query_params.get('search', '')
        practice_area_qs = practice_area_qs.filter(
            title__icontains=search_text
        )

        page = self.paginate_queryset(queryset=practice_area_qs)
        serializer = PostedMattersByPracticeAreaSerializer(
            page,
            many=True,
            context={"request": request}
        )

        ordering_fields = request.query_params.getlist('ordering', [])

        data = serializer.data
        for field in ordering_fields:
            reverse = False
            if field.startswith('-'):
                reverse = True
                field = field[1:]
            data = sorted(
                serializer.data,
                key=lambda k: (k[field] is not None, k[field]),
                reverse=reverse
            )

        if page is not None:
            return self.paginator.get_paginated_response(data)

        return Response(
            data=data,
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True)
    def deactivate(self, request, *args, **kwargs):
        """Deactivates posted matter"""
        posted_matter = self.get_object()
        try:
            posted_matter.deactivate()
            posted_matter.save()
            post_inactivated.send(
                sender=PostedMatter, instance=self, user=request.user
            )
        except TransitionNotAllowed:
            raise WrongTransitionException
        serializer = self.serializer_class(posted_matter)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True)
    def reactivate(self, request, *args, **kwargs):
        """Reactivates posted matter"""
        posted_matter = self.get_object()
        try:
            posted_matter.reactivate()
            posted_matter.save()
            post_reactivated.send(
                sender=PostedMatter, instance=self, user=request.user
            )
        except TransitionNotAllowed:
            raise WrongTransitionException
        serializer = self.serializer_class(posted_matter)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        """Disable posted matter"""
        posted_matter = self.get_object()
        proposals = posted_matter.proposals.filter(
            status=Proposal.STATUS_ACCEPTED
        )
        if len(proposals) == 0:
            self.perform_destroy(posted_matter)
            posted_matter.proposals.all().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        for proposal in proposals:
            proposal.is_hidden_for_client = request.user.is_client
            proposal.is_hidden_for_attorney = request.user.is_attorney
            proposal.save()
        if request.user.is_client:
            posted_matter.is_hidden_for_client = True
            posted_matter.save()
        elif request.user.is_attorney:
            posted_matter.is_hidden_for_attorney = True
            posted_matter.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProposalViewSet(CRUDViewSet):
    """
        View set for Proposal view
        provide basic CRUD operations.
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = ProposalSerializer
    search_fields = ('title', 'description')
    queryset = Proposal.objects.select_related(
        'attorney',
        'attorney__user',
        'currency'
    ).exclude(status=Proposal.STATUS_WITHDRAWN)
    filterset_class = filters.ProposalFilter
    ordering_fields = (
        'created',
        'modified',
        'status_modified'
    )

    @action(methods=['post'], detail=True)
    def withdraw(self, request, *args, **kwargs):
        """View for attorney proposal withdrawal."""
        proposal = self.get_object()
        proposal.status = Proposal.STATUS_WITHDRAWN
        proposal.status_modified = timezone.now()
        proposal.save()
        proposal_withdrawn.send(
            sender=Proposal, instance=proposal, user=request.user
        )
        serializer = self.serializer_class(proposal)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True)
    def accept(self, request, *args, **kwargs):
        """View for proposal acceptance."""
        proposal = self.get_object()
        if proposal.post.status == PostedMatter.STATUS_INACTIVE:
            return Response(
                data={"detail": "Can not accept this proposal"},
                status=status.HTTP_400_BAD_REQUEST
            )
        proposal.status = Proposal.STATUS_ACCEPTED
        proposal.status_modified = timezone.now()
        proposal.save()
        PostedMatter.objects.filter(pk=proposal.post.pk).update(
            status=PostedMatter.STATUS_INACTIVE
        )
        proposal_accepted.send(
            sender=Proposal, instance=proposal, user=request.user
        )
        serializer = self.serializer_class(proposal)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True)
    def revoke(self, request, *args, **kwargs):
        """View to revoke proposal."""
        proposal = self.get_object()
        proposal.status = Proposal.STATUS_REVOKED
        proposal.status_modified = timezone.now()
        proposal.save()
        PostedMatter.objects.filter(pk=proposal.post.pk).update(
            status=PostedMatter.STATUS_ACTIVE
        )
        serializer = self.serializer_class(proposal)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )
