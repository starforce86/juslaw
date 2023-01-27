from datetime import datetime, timedelta

from django.http import Http404

from rest_framework import generics, response, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

import stripe
from dateutil.relativedelta import relativedelta
from djstripe import models as stripe_models
from djstripe import settings as djstripe_settings

from apps.core.api.views import BaseViewSet, ReadOnlyViewSet
from apps.finance.api import serializers
from apps.finance.models import FinanceProfile, PlanProxy, SubscriptionProxy
from apps.finance.services import stripe_subscriptions_service
from apps.users.api.permissions import IsAttorneyFreeAccess
from apps.users.models import AppUser

stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY

__all__ = (
    'AppUserPaymentSubscriptionView',
    'PlanViewSet',
    'CurrentCustomerView',
    'SubscriptionOptions',
)


class AppUserPaymentSubscriptionView(GenericViewSet):
    """View for users payments subscriptions.

    This view provides methods for frontend to work with Stripe and also
    prepares and stores in DB payment subscriptions for user.

    """
    pagination_class = None
    permission_classes = (AllowAny,)

    @action(methods=['GET'], detail=False, url_path='get-setup-intent')
    def get_setup_intent(self, request):
        """Prepare SetupIntent `client_secret` key for new customer.

        This endpoint gets SetupIntent `client_secret` key for a new customer
        from Stripe. Later it is used by frontend to collect card details and
        prepare user payment methods with Stripe.

        We don't need to store SetupIntent and its relation to AppUser
        (Customer) in DB cause SetupIntent is a not long-lived entity cause it
        can expire after 24h.

        Stripe documentation:
            https://stripe.com/docs/api#setup_intents
        Card saving workflow:
            https://stripe.com/docs/payments/save-and-reuse

        """
        stripe_setup_intent = stripe_models.SetupIntent._api_create()
        serializer = serializers.SetupIntentTokenSerializer(
            stripe_setup_intent
        )
        return response.Response(
            status=status.HTTP_200_OK, data=serializer.data
        )


class PlanViewSet(ReadOnlyViewSet):
    """Viewset for stripe payments Plans.

    This viewset just returns available for JLP project payment plans
    (subscription types).

    """
    base_permission_classes = AllowAny,
    queryset = PlanProxy.objects.active()
    serializer_class = serializers.PlanSerializer

    def get_queryset(self):
        """Get plans with user type"""
        qp = self.request.query_params
        user_type = qp.get('type')
        if user_type is None:
            return super().get_queryset()
        plan_list = []
        for obj in AppUser.objects.all():
            if not hasattr(obj, 'finance_profile'):
                continue
            plan = obj.finance_profile.initial_plan
            if plan is None:
                continue
            if obj.user_type == user_type:
                plan_list.append(plan)
        plan_list = list(set(plan_list))
        return plan_list


class CurrentCustomerView(
    generics.RetrieveAPIView,
    generics.UpdateAPIView,
    generics.GenericAPIView
):
    """Retrieve current user Stripe customer."""
    serializer_class = serializers.CurrentCustomerSerializer
    permission_classes = IsAuthenticated, IsAttorneyFreeAccess

    def get_object(self):
        """Get user's customer (stripe profile)."""
        user = self.request.user
        if not user.customer:
            raise Http404
        return user.customer


class SubscriptionViewSet(BaseViewSet):
    """View for creating attorney subscription
    """

    serializer_class = serializers.NewSubscriptionsSerializer
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        """Create subscription
        """
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        user_id = data.pop('user_id', None)
        plan_id = data.pop('plan_id', None)
        token = data.pop('token', None)
        try:
            user = AppUser.objects.get(id=user_id)
            customer = stripe_subscriptions_service.\
                create_customer_with_attached_card(
                    user=user,
                    payment_method=token
                )

            six_months = datetime.now() + relativedelta(months=+6)
            trial_end = (six_months - datetime(1970, 1, 1)) / timedelta(
                seconds=1
            )
            subscription = SubscriptionProxy.create(
                customer_id=customer.id,
                plan_id=plan_id,
                trial_end=round(trial_end)
            )
            user.active_subscription = subscription
            user.save()
            plan = PlanProxy.objects.get(id=plan_id)
            FinanceProfile.objects.update_or_create(
                user=user,
                defaults={'initial_plan': plan}
            )
            return Response(status=status.HTTP_200_OK, data={
                "success": True
            })
        except stripe.error.StripeError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "success": False,
                "detail": str(e.user_message)
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "success": False,
                "detail": str(e)
            })


class PaymentMethodViewSet(BaseViewSet):
    """View for creating payment method"""

    serializer_class = serializers.PaymentMethodSerializer
    permission_classes = (IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        """List payment method source"""
        try:
            user = request.user
            payment_methods = []
            if user.customer:
                payment_methods = stripe_models.PaymentMethod.objects.filter(
                    customer_id=user.customer.djstripe_id
                )
            page = self.paginate_queryset(queryset=payment_methods)
            data = serializers.CurrentPaymentMethodSerializer(
                instance=payment_methods,
                many=True
            ).data
            if page is not None:
                return self.get_paginated_response(data)
            else:
                return Response(
                    data=data,
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "detail": str(e)
            })

    def create(self, request, *args, **kwargs):
        """Create payment method source"""
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        token = data.pop('token', None)
        try:
            user = request.user
            stripe_subscriptions_service.\
                create_customer_with_attached_card(
                    user=user, payment_method=token
                )
            FinanceProfile.objects.update_or_create(user=user)
            return Response(status=status.HTTP_200_OK, data={
                "success": True
            })
        except stripe.error.StripeError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "success": False,
                "detail": str(e.user_message)
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "success": False,
                "detail": str(e)
            })

    def destroy(self, request, pk=None):
        try:
            payment_method = stripe_models.PaymentMethod.objects.get(id=pk)
            payment_method.detach()
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "detail": "Unfortunately, payment method was not removed"
            })
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionOptions(BaseViewSet):
    """View for changing attorney subscription.

    The following actions are available:
        1. Unsubscribing subscription
        2. Reactivation subscription
        3. Get previewing by switching plan
        4. Switching subscription plan

    """
    base_filter_backends = None
    pagination_class = None

    serializer_class = serializers.SubscriptionSerializer
    permission_classes = IsAuthenticated, IsAttorneyFreeAccess

    serializers_map = {
        'cancel_subscription': None,
        'reactivate_subscription': None,
        'change_subscription': serializers.SubscriptionSwitchSerializer,
        'preview_change_subscription':
            serializers.SubscriptionSwitchSerializer,
    }

    @action(methods=['post'], url_path='cancel', detail=False)
    def cancel_subscription(self, request, *args, **kwargs):
        """Cancel current subscription (active or trialing)

        Unsubscribing subscription
        Cancel the subscription at the end of the current billing period
        (i.e., for the duration of time the attorney has already paid for)

        If attorney has next subscription - then it will be canceled and
        deleted

        """
        cancel_subscription = stripe_subscriptions_service(
            request.user
        ).cancel_current_subscription()
        result = self.serializer_class(cancel_subscription)
        return Response(data=result.data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path='reactivate', detail=False)
    def reactivate_subscription(self, request, *args, **kwargs):
        """Reactivates cancelled subscription

        Reactivation subscription
        If an attorney’s subscription is canceled and it has not yet reached
        the end of the billing period, it can be reactivated

        """
        reactivate_subscription = stripe_subscriptions_service(
            request.user
        ).reactivate_cancelled_subscription()
        result = self.serializer_class(reactivate_subscription)
        return Response(data=result.data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path='change/preview', detail=False)
    def preview_change_subscription(self, request, *args, **kwargs):
        """Return prepared info about switching plan

        Prepare attorney for any additional expense that comes with a
        plan change or change renewal date

        """
        serializer_class = super().get_serializer_class()
        serializer = serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)
        plan = serializer.validated_data['plan']
        preview = stripe_subscriptions_service(
            request.user
        ).calc_subscription_changing_cost(new_plan=plan)

        result = serializers.SubscriptionSwitchPreviewSerializer(preview)
        return Response(data=result.data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path='change', detail=False)
    def change_subscription(self, request, *args, **kwargs):
        """Change attorney subscription plan

        1. `Downgrade subscription`
        When a attorney's plan downgrades to `standard`, they will
        keep their premium subscription until the next billing date for
        `active` subscriptions

        2. `Upgrade subscription`
        When a attorney's plan change to `premium` for `active` subscription,
        then:
            * Switch your premium subscription immediately
            * Generate one-off invoice for attorney pay the price difference
            when switching to a more expensive plan

        For `trialing` subscriptions it doesn't matter what is a new plan -
        subscriptions would be changed immediately and no new upcoming invoices
        will be generated.

        # TODO: Move to separate API
        If the attorney does not have a active subscription - created new.

        """
        serializer_class = super().get_serializer_class()
        serializer = serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)
        plan = serializer.validated_data['plan']
        renewed_subscription = stripe_subscriptions_service(
            request.user
        ).change_subscription_plan(new_plan=plan)

        result = serializers.SubscriptionSerializer(
            renewed_subscription
        )
        return Response(data=result.data, status=status.HTTP_200_OK)
