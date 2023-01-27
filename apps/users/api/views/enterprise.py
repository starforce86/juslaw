from django.conf import settings
from django.db import transaction

from rest_framework import generics, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.business.api.serializers.external_overview import (
    EnterpriseDetailedOverviewSerializer,
)
from apps.business.models.matter import Lead
from apps.core.api.views import BaseViewSet
from apps.finance.services import stripe_subscriptions_service

from ...api import permissions, serializers
from ...models import Attorney, Enterprise, Paralegal
from ..filters import EnterpriseFilter
from .utils.verification import complete_signup


class EnterpriseViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """View for registration and search of enterprise.

    Endpoint for registration, retrieval and search of user enterprise profile

    To get enterprise, that users follows you should do request like this:
    `users/enterprises/?followed=true`.

    This view is read only(except for registration), since user can only edit
    it's own enterprise profile.
    Note: user can create enterprise profile only once
    Edit functionality is presented in CurrentEnterpriseView

    """
    permissions_map = {
        'default': (AllowAny,),
        'follow': (permissions.CanFollow, permissions.IsEnterpriseAdmin,),
        'unfollow': (permissions.CanFollow, permissions.IsEnterpriseAdmin,),
        'onboarding': (permissions.IsEnterpriseAdminOf, IsAuthenticated),
        'add_contact': (permissions.IsEnterpriseAdmin, IsAuthenticated),
        'remove_contact': (permissions.IsEnterpriseAdmin, IsAuthenticated),
        'overview': (permissions.IsEnterpriseAdmin, IsAuthenticated),
    }
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.EnterpriseAndAdminUserSerializer
    queryset = Enterprise.objects.real_users().verified().select_related(
        'user',
    ).prefetch_related(
        'followers',
        'user__specialities',
        'firm_size',
        'firm_locations',
        'firm_locations__country',
        'firm_locations__state',
        'firm_locations__city',
        'firm_locations__city__region',
        'team_members'
    )
    filterset_class = EnterpriseFilter
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
    #    for example when you have view set at `users` and at
    #    `users/enterprise`
    #    without it view set will collapse with at `users` in a way that
    #    users view set we use 'enterprise' part of url as pk for search in
    #    retrieve method
    lookup_value_regex = '[0-9]+'

    def get_object(self):
        return Enterprise.objects.get(user_id=self.kwargs['pk'])

    def create(self, request, *args, **kwargs):
        """Register user and return enterprise profile.

        There is following workflow:
        1. Create new user
        2. Create enterprise and related objects
        3. Create new customer with set up payment method (based on related
        SetupIntent).

        """
        enterprise_serializer = serializers.EnterpriseRegisterSerializer(
            data=request.data
        )
        enterprise_serializer.is_valid(raise_exception=True)

        if request.data.get('role') == Enterprise.ROLE_ATTORNEY:
            serializer = serializers.AttorneyRegisterSerializer(
                data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            #  If the view produces an exception, rolls back the transaction
            #  of creation user and attorney.
            headers = self.get_success_headers(data)
            payment_method = data.get('payment_method', None)
            with transaction.atomic():
                user = serializer.save(self.request)
                enterprise_serializer.create_entry(user)

                attorney = Attorney.objects.get(pk=user.pk)
                attorney.enterprise = user.owned_enterprise
                attorney.save()
                if payment_method is not None:
                    stripe_subscriptions_service. \
                        create_customer_with_attached_card(
                            user=user,
                            payment_method=payment_method
                        )
            serializer = serializers.AttorneySerializer(
                instance=attorney
            )
        else:
            serializer = serializers.ParalegalRegisterSerializer(
                data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            #  If the view produces an exception, rolls back the transaction
            #  of creation user and paralegal.
            headers = self.get_success_headers(data)
            payment_method = data.get('payment_method', None)
            with transaction.atomic():
                user = serializer.save(self.request)
                enterprise_serializer.create_entry(user)

                paralegal = Paralegal.objects.get(pk=user.pk)
                paralegal.enterprise = user.owned_enterprise
                paralegal.save()
                if payment_method is not None:
                    stripe_subscriptions_service. \
                        create_customer_with_attached_card(
                            user=user,
                            payment_method=payment_method
                        )
            serializer = serializers.ParalegalSerializer(
                instance=paralegal
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
        """Follow enterprise."""
        enterprise = self.get_object()
        enterprise.followers.add(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='unfollow', )
    def unfollow(self, request, **kwargs):
        """Unfollow enterprise."""
        enterprise = self.get_object()
        enterprise.followers.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='onboarding', )
    def onboarding(self, request, **kwargs):
        """Onboarding enterprise"""
        enterprise = Enterprise.objects.get(user_id=self.kwargs['pk'])
        if not enterprise:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "success": False,
                "detail": "Not found enterprise user"
            })
        serializer = serializers.EnterpriseOnboardingSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        enterprise = serializer.update(enterprise.id, data)
        serializer = serializers.EnterpriseAndAdminUserSerializer(
            instance=enterprise
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False, url_path='validate-registration')
    def validate_registration(self, request, **kwargs):
        """Validate enterprise registration steps.

        App has a multistage registration process on 3 pages, which is not
        convenient to validate with one request. To make it more easy to use
        there are added separate API endpoints to validate each registration
        page separately. It allows to prevent redirecting user to next
        registration stage if current one is not valid in frontend.

        Current registration validation allows to check only steps:

            - 1st - `email`, `password1`, `password2`
            - 2d - all left enterprise registration fields except `Stripe`
                payment info.

        """
        stage_serializer = serializers.EnterpriseRegisterValidateSerializer(
            data=request.query_params
        )
        stage_serializer.is_valid(raise_exception=True)
        stage = stage_serializer.validated_data['stage']
        reg_stage_serializer_map = {
            'first': serializers.EnterpriseRegisterValidFirstStepSerializer,
            'second': serializers.EnterpriseRegisterValidSecondStepSerializer
        }
        serializer = reg_stage_serializer_map[stage](data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'])
    def add_contact(self, request, *args, **kwargs):
        """Add client as contact"""
        enterprise = self.get_object()
        client_id = request.data.get("client", None)
        try:
            Lead.objects.get_or_create(enterprise=enterprise, client=client_id)
            return Response(
                status=status.HTTP_200_OK,
                data={"success": True}
            )
        except ValueError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"success": False}
            )

    @action(detail=True, methods=['DELETE'])
    def remove_contact(self, request, *args, **kwargs):
        """Add client as contact"""
        enterprise = self.get_object()
        client_id = request.data.get("client", None)
        Lead.objects.filter(enterprise=enterprise, client=client_id).delete()
        return Response(
            status=status.HTTP_200_OK,
            data={"success": True}
        )

    @action(detail=True, methods=['GET'])
    def overview(self, request, *args, **kwargs):
        """Returns Overview details for paralegal dashboard."""
        paralegal = self.get_object()
        serializer = EnterpriseDetailedOverviewSerializer(paralegal, context={
            'request': request
        })
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )


class CurrentEnterpriseView(
    generics.UpdateAPIView,
    generics.RetrieveAPIView
):
    """Retrieve and update user's enterprise profile.

    Accepts GET, PUT and PATCH methods.
    """
    serializer_class = serializers.EnterpriseAndAdminUserSerializer
    permission_classes = (
        IsAuthenticated,
        permissions.IsEnterpriseAdmin,
    )

    def get_object(self):
        """Get user's enterprise profile."""
        return self.request.user.owned_enterprise

    def get_serializer_class(self):
        """Return serializer for update on `PUT` or `PATCH` requests.

        Can't use ActionSerializerMixin since it's not view-set.

        """
        if self.request.method in ('PUT', 'PATCH',):
            return serializers.UpdateEnterpriseSerializer
        return super().get_serializer_class()
