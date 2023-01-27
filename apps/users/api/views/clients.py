from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import generics, mixins, response, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.business.models.posted_matters import PostedMatter

from ....business.api.serializers.external_overview import (
    ClientOverviewSerializer,
)
from ....business.models import Matter, Lead
from ....core.api.views import BaseViewSet
from ....users import models
from ...api import filters, permissions, serializers
from ..filters import AttorneyParalegalSearchFilter
from ..serializers.extra import AttorneyParalegalSearchSerializer
from .utils.verification import complete_signup


class ClientViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    BaseViewSet
):
    """App user endpoint for search users and registration."""
    serializer_class = serializers.ClientSerializer
    queryset = models.Client.objects.select_related(
        'user',
        'country',
        'state',
        'city',
        'city__region',
        'timezone',
    ).prefetch_related(
        'user__specialities',
        'user__activities',
        'user__activities__matter',
        'matters__attorney',
        'matters',
    )
    permissions_map = {
        'create': (AllowAny,),
    }
    filterset_class = filters.ClientFilter
    search_fields = [
        '@user__first_name',
        '@user__last_name',
        'user__email',
        'organization_name',
    ]
    ordering_fields = [
        'modified',
        'user__email',
        'user__first_name',
        'user__last_name',
        'organization_name',
    ]
    # Explanation:
    #    We changed lookup_value_regex to avoid views sets urls collapsing
    #    for example when you have view set at `users` and at `users/attorney`,
    #    without it view set will collapse with at `users` in a way that
    #    users view set we use 'attorney' part of url as pk for search in
    #    retrieve method.
    lookup_value_regex = '[0-9]+'

    def get_queryset(self):
        """Add attorney_id qs using query params"""
        qs = super().get_queryset()
        qp = self.request.query_params
        attorney_id = qp.get('attorney', None)
        if attorney_id is not None:
            return qs.filter(
                matters__attorney_id=qp.get('attorney')
            ).distinct()
        return qs

    def create(self, request, *args, **kwargs):
        """Register user and return client profile."""
        is_by_invite = request.data.get('invite_uuid', False)
        if is_by_invite:
            invite = models.Invite.objects.get(pk=request.data.get('invite_uuid'))
            invite_serializer = serializers.InviteSerializer(invite)
            new_client_data = invite_serializer.data
        else:
            new_client_data = {}
        new_client_data.update(request.data)
        serializer = serializers.ClientRegisterSerializer(data=new_client_data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save(request)

            if is_by_invite:
                for matter in Matter.get_by_invite(invite):
                    matter.client = user.client
                    matter.invite = None
                    matter.save()

                Lead.objects.create(
                    client=user.client,
                    attorney_id=(invite.inviter_id if invite.inviter.is_attorney else None),
                    paralegal_id=(invite.inviter_id if invite.inviter.is_paralegal else None),
                    enterprise_id=(invite.inviter_id if invite.inviter.is_enterprise else None)
                )

                invite.user = user
                invite.inviter = None
                invite.save()

        headers = self.get_success_headers(serializer.validated_data)
        serializer = serializers.ClientSerializer(
            instance=user.client
        )

        complete_signup(
            self.request._request,
            user,
            settings.ACCOUNT_EMAIL_VERIFICATION,
            None
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(
        detail=True, methods=['GET'],
        url_path='matter_overview/(?P<matter_id>[^/.]+)'
    )
    def matter_overview(self, request, *args, **kwargs):
        """
        Validates client permissions and
        returns the list of matters (Overviews)
        """
        client = self.get_object()
        from apps.business.api.serializers.matter import (
            MatterOverviewSerializer,
        )
        try:
            matter = client.matters.get(id=self.kwargs['matter_id'])
            serializer = MatterOverviewSerializer(
                matter,
                context={'request': request},
            )
            return response.Response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['GET'])
    def overview(self, request, *args, **kwargs):
        """
        Validates client permissions and
        returns the dashboard overview details
        """
        client = self.get_object()
        serializer = ClientOverviewSerializer(
            client, context={'request': request},
        )
        return response.Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['GET'])
    def posted_matters(self, request, *args, **kwargs):
        """
            Validates client permissions and
            returns matters posted by client
        """
        is_active = request.query_params.get('is_active', '')
        is_hidden_for_client = request.query_params.get('is_hidden_for_client')
        client = self.get_object()
        from apps.business.api.serializers.posted_matters import (
            PostedMatterSerializer,
        )
        posted_matters = client.posted_matters
        if is_active == 'true':
            posted_matters = posted_matters.filter(
                status=PostedMatter.STATUS_ACTIVE
            )
        elif is_active == 'false':
            posted_matters = posted_matters.filter(
                status=PostedMatter.STATUS_INACTIVE
            )
        if is_hidden_for_client == 'true':
            posted_matters = posted_matters.filter(is_hidden_for_client=True)
        elif is_hidden_for_client == 'false':
            posted_matters = posted_matters.filter(is_hidden_for_client=False)

        page = self.paginate_queryset(queryset=posted_matters.all())

        if page is not None:
            serializer = PostedMatterSerializer(posted_matters, many=True)
            return self.paginator.get_paginated_response(data=serializer.data)

        serializer = PostedMatterSerializer(
            posted_matters, many=True
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def search_attorneys_and_paralegals(self, request, *args, **kwargs):
        """Search Attorney and paralegals."""
        filterer = AttorneyParalegalSearchFilter()
        is_sharable = request.query_params.get('sharable', 'false')
        if is_sharable == 'true':
            users = models.AppUser.objects.available_for_share()
            attorneys = models.Attorney.objects.filter(user__in=users)
            paralegals = models.Paralegal.objects.filter(user__in=users)
        else:
            attorneys = models.Attorney.objects.verified()
            paralegals = models.Paralegal.objects.verified()
        attorneys = filterer.filter_queryset(request, attorneys, None)
        paralegals = filterer.filter_queryset(request, paralegals, None)

        searched_items = set(attorneys) | set(paralegals)

        page = self.paginate_queryset(queryset=list(searched_items))
        if page is not None:
            serializer = AttorneyParalegalSearchSerializer(page, many=True)
            return self.paginator.get_paginated_response(data=serializer.data)

        serializer = AttorneyParalegalSearchSerializer(
            searched_items,
            many=True
        )
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def get_contacts(self, request, *args, **kwargs):
        """returns list of client contacts"""
        client = self.get_object()
        contacts = client.contacts()
        contact_users = get_user_model().objects.filter(id__in=contacts)
        page = self.paginate_queryset(queryset=list(contact_users))
        serializer = serializers.AppUserShortSerializer(
            contact_users, many=True
        )
        if page is not None:
            serializer = serializers.AppUserShortSerializer(page, many=True)
            return self.paginator.get_paginated_response(data=serializer.data)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data
        )


class CurrentClientView(
    generics.UpdateAPIView,
    generics.RetrieveAPIView,
    generics.GenericAPIView,
):
    """Retrieve and update user's client profile.

    Accepts GET, PUT and PATCH methods.
    Read-only fields: user, specialities_data.
    """
    serializer_class = serializers.ClientSerializer
    permission_classes = IsAuthenticated, permissions.IsClient

    def get_serializer_class(self):
        """Return serializer for update on `PUT` or `PATCH` requests."""
        if self.request.method in ('PUT', 'PATCH',):
            return serializers.UpdateClientSerializer
        return super().get_serializer_class()

    def get_object(self):
        """Get user's client profile."""
        return self.request.user.client


class CurrentClientFavoriteViewSet(
    mixins.UpdateModelMixin,
    BaseViewSet
):
    """Retrieve client's favorite attorney"""

    serializer_class = serializers.ClientFavoriteAttorneySerializer
    permission_classes = IsAuthenticated, permissions.IsClient

    def list(self, request, *args, **kwargs):
        client = request.user.client
        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(client).data
        )

    def update(self, request, pk=None):
        client = request.user.client
        if models.Attorney.objects.filter(pk=pk).exists():
            client.favorite_attorneys.add(pk)
            attorney = models.Attorney.objects.get(pk=pk)
            attorney.followers.add(client.user)
            return Response(
                status=status.HTTP_200_OK,
                data=self.serializer_class(client).data
            )
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": "Attorney does not exist"}
            )

    def destroy(self, request, pk=None):
        client = request.user.client
        if models.Attorney.objects.filter(pk=pk).exists():
            client.favorite_attorneys.remove(pk)
            attorney = models.Attorney.objects.get(pk=pk)
            attorney.followers.remove(client.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": "Attorney does not exist"}
            )
