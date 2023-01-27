from django.conf import settings
from django.db import transaction
from django.db.models.query import Prefetch
from django.shortcuts import get_object_or_404

from rest_framework import generics, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.business.api.serializers.external_overview import (
    LeadAndClientSerializer,
    ParalegalDetailedOverviewSerializer,
)
from apps.business.models.matter import Lead
from apps.core.api.views import BaseViewSet
from apps.finance.services import stripe_subscriptions_service

from ...api import permissions, serializers
from ...models import Client, Invite, Paralegal
from ..filters import LeadClientFilter, LeadClientSearchFilter, ParalegalFilter
from .utils.verification import complete_signup


class ParalegalViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """View for registration and search of paralegals.

    Endpoint for registration, retrieval and search of users' paralegal profile

    To get paralegals, that users follows you should do request like this:
    `users/paralegals/?followed=true`.

    This view is read only(except for registration), since user can only edit
    it's own paralegal profile.
    Note: user can create paralegal profile only once
    Edit functionality is presented in CurrentParalegalView

    """
    permissions_map = {
        'default': (AllowAny,),
        'follow': (permissions.CanFollow,),
        'unfollow': (permissions.CanFollow,),
    }
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ParalegalSerializer
    queryset = Paralegal.objects.real_users().verified().select_related(
        'user',
    ).prefetch_related(
        'followers',
        'practice_jurisdictions',
        'education',
        'education__university',
        'user__specialities',
        'fee_types',
        'registration_attachments',
    )
    filterset_class = ParalegalFilter
    search_fields = [
        '@user__first_name',
        '@user__last_name',
        'user__email',
    ]
    ordering_fields = [
        'featured',
        'distance',
        'modified',
        'user__email',
        'user__first_name',
        'user__last_name',
    ]
    # Explanation:
    #    We changed lookup_value_regex to avoid views sets urls collapsing
    #    for example when you have view set at `users` and at `users/paralegal`
    #    without it view set will collapse with at `users` in a way that
    #    users view set we use 'paralegal' part of url as pk for search in
    #    retrieve method
    lookup_value_regex = '[0-9]+'

    def get_queryset(self):
        """Add distance to qs, using data from query_params."""
        qs = super().get_queryset()
        qp = self.request.query_params
        return qs.with_distance(
            longitude=qp.get('longitude'),
            latitude=qp.get('latitude')
        )

    def create(self, request, *args, **kwargs):
        """Register user and return paralegal profile.

        There is following workflow:
        1. Create new user
        2. Create paralegal and related objects
        3. Create new customer with set up payment method (based on related
        SetupIntent).

        """
        serializer = serializers.ParalegalRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        #  If the view produces an exception, rolls back the transaction
        #  of creation user and paralegal.
        headers = self.get_success_headers(data)
        payment_method = data.get('payment_method', None)
        with transaction.atomic():
            user = serializer.save(self.request)
            if payment_method is not None:
                stripe_subscriptions_service.\
                    create_customer_with_attached_card(
                        user=user,
                        payment_method=payment_method
                    )
        serializer = serializers.ParalegalSerializer(
            instance=user.paralegal
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

    @action(methods=['post'], detail=True, url_path='follow', )
    def follow(self, request, **kwargs):
        """Follow paralegal."""
        paralegal = self.get_object()
        paralegal.followers.add(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='unfollow', )
    def unfollow(self, request, **kwargs):
        """Unfollow paralegal."""
        paralegal = self.get_object()
        paralegal.followers.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='onboarding', )
    def onboarding(self, request, **kwargs):
        """Onboarding paralegal"""
        paralegal_id = self.kwargs['pk']
        serializer = serializers.ParalegalOnboardingSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        paralegal = serializer.update(paralegal_id, data)
        serializer = serializers.ParalegalSerializer(
            instance=paralegal
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False, url_path='validate-registration')
    def validate_registration(self, request, **kwargs):
        """Validate paralegal registration steps.

        App has a multistage registration process on 3 pages, which is not
        convenient to validate with one request. To make it more easy to use
        there are added separate API endpoints to validate each registration
        page separately. It allows to prevent redirecting user to next
        registration stage if current one is not valid in frontend.

        Current registration validation allows to check only steps:

            - 1st - `email`, `password1`, `password2`
            - 2d - all left paralegal registration fields except `Stripe`
                payment info.

        """
        stage_serializer = serializers.ParalegalRegisterValidateSerializer(
            data=request.query_params
        )
        stage_serializer.is_valid(raise_exception=True)
        stage = stage_serializer.validated_data['stage']
        reg_stage_serializer_map = {
            'first': serializers.ParalegalRegisterValidateFirstStepSerializer,
            'second': serializers.ParalegalRegisterValidateSecondStepSerializer
        }
        serializer = reg_stage_serializer_map[stage](data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['GET'])
    def leads_and_clients(self, request, *args, **kwargs):
        """Returns attorney's leads and clients."""
        paralegal = get_object_or_404(self.queryset, **kwargs)
        try:
            search_filter = LeadClientSearchFilter()
            type_filter = LeadClientFilter()

            leads_clients = Client.objects.select_related(
                    'user',
                    'country',
                    'state',
                    'city',
                    'city__region',
                ).prefetch_related(
                    Prefetch(
                        'leads',
                        queryset=Lead.objects.filter(
                            status=Lead.STATUS_CONVERTED
                        )
                    ),
                ).filter(leads__paralegal=paralegal)
            leads_clients = search_filter.search_lead_client(
                request, leads_clients
            )
            leads_clients = type_filter.filter_type(request, leads_clients)

            invites = Invite.get_pending_paralegal_invites(paralegal).\
                select_related(
                    'country',
                    'state',
                    'city',
                    'city__region',
                ).prefetch_related(
                    'matters'
                )
            invites = search_filter.search_lead_client(request, invites)
            invites = type_filter.filter_type(request, invites)

            leads_and_clients = set(leads_clients) | set(invites)

            page = self.paginate_queryset(queryset=list(leads_and_clients))
            ordering_fields = request.GET.getlist('ordering', [])
            if page is not None:
                serializer = LeadAndClientSerializer(
                    page, many=True,
                    context={'request': request}
                )
            else:
                serializer = LeadAndClientSerializer(
                    leads_and_clients, many=True,
                    context={'request': request}
                )
            data = serializer.data
            for field in ordering_fields:
                reverse = False
                if field.startswith('-'):
                    reverse = True
                    field = field[1:]
                data = sorted(
                    data,
                    key=lambda k: (k[field] is not None, k[field]),
                    reverse=reverse
                )
            if page is not None:
                return self.get_paginated_response(data)
            else:
                return Response(
                    data=data,
                    status=status.HTTP_200_OK
                )
        except Exception:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['POST'])
    def add_contact(self, request, *args, **kwargs):
        """Add client as contact"""
        paralegal = get_object_or_404(self.queryset, **kwargs)
        user_id = request.data.get("user_id", None)
        try:
            client = Client.objects.get(pk=user_id)
            Lead.objects.get_or_create(paralegal=paralegal, client=client)
            return Response(
                status=status.HTTP_200_OK,
                data={"success": True}
            )
        except Client.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "success": False,
                    "detail": "Client profile does not exist"
                }
            )
        except ValueError as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "success": False,
                    "detail": str(e)
                }
            )

    @action(detail=True, methods=['DELETE'])
    def remove_contact(self, request, *args, **kwargs):
        """Add client as contact"""
        paralegal = get_object_or_404(self.queryset, **kwargs)
        try:
            user_id = request.data.get("user_id", None)
            is_invite = False
            try:
                is_invite = not isinstance(int(user_id), int)
            except ValueError:
                is_invite = True
            if is_invite:
                Invite.objects.filter(uuid=user_id).delete()
            else:
                Lead.objects.filter(
                    paralegal=paralegal, client=user_id
                ).delete()
            return Response(
                data={"success": True},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(e)
            return Response(
                data={"success": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['POST'])
    def change_user_type(self, request, *args, **kwargs):
        """Paralegal allow to change user types(lead, client)"""
        paralegal = self.get_object()
        user_id = request.data.get('user_id')
        type = request.data.get('type', 'client')
        try:
            is_invite = False
            try:
                is_invite = not isinstance(int(user_id), int)
            except ValueError:
                is_invite = True
            if is_invite:
                Invite.objects.filter(uuid=user_id).update(client_type=type)
            else:
                lead = paralegal.leads.get(client=user_id)
                if type == 'client':
                    lead.status = Lead.STATUS_CONVERTED
                elif type == 'lead':
                    lead.status = Lead.STATUS_ACTIVE
                lead.save()
        except Lead.DoesNotExist:
            return Response(
                data={"success": False},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            data={"success": True},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['GET'])
    def overview(self, request, *args, **kwargs):
        """Returns Overview details for paralegal dashboard."""
        paralegal = self.get_object()
        serializer = ParalegalDetailedOverviewSerializer(paralegal, context={
            'request': request
        })
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )


class CurrentParalegalView(
    generics.UpdateAPIView,
    generics.RetrieveAPIView,
    generics.GenericAPIView
):
    """Retrieve and update user's paralegal profile.

    Accepts GET, PUT and PATCH methods.
    Read-only fields:
        * first_name
        * last_name
        * user
        * is_verified
        * specialities_data
        * fee_types_data
    """
    serializer_class = serializers.ParalegalSerializer
    permission_classes = (
        IsAuthenticated,
        permissions.IsParalegal,
    )

    def get_object(self):
        """Get user's paralegal profile."""
        return self.request.user.paralegal

    def get_serializer_class(self):
        """Return serializer for update on `PUT` or `PATCH` requests.

        Can't use ActionSerializerMixin since it's not view-set.

        """
        if self.request.method in ('PUT', 'PATCH',):
            return serializers.UpdateParalegalSerializer
        return super().get_serializer_class()
