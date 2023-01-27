import logging
import os
import uuid

from django.conf import settings
from django.core.cache import cache
from django.http import Http404

from rest_framework import response, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated

import stripe
from constance import config

from libs.api.serializers.serializers import URLSerializer

from apps.core.api.views import BaseViewSet
from apps.users.api.permissions import IsAttorneyHasActiveSubscription
from apps.users.models import AppUser

from ...models import AccountProxy, FinanceProfile
from ...services import stripe_deposits_service
from ..permissions import IsAttorneyHasNoConnectedAccount
from ..serializers import (
    AccountProxySerializer,
    ErrorCallbackSerializer,
    SuccessCallbackSerializer,
)

__all__ = (
    'AccountAuthViewSet',
    'CurrentAccountViewSet',
)


logger = logging.getLogger('stripe')


class AccountAuthViewSet(BaseViewSet):
    """Viewset to set up stripe accounts for attorney's direct deposits.

    To make available direct payments to some attorney, he needs to create
    stripe `Express` account through our app, fill required by stripe fields
    and wait until his information would be verified by stripe.

    This view provides possibility to initiate stripe `Express` account
    creation and process stripe callback after user's registration.

    Express account docs:
        https://stripe.com/docs/connect/express-accounts
    Whole account registration process:
        https://stripe.com/docs/connect/collect-then-transfer-guide

    """
    base_filter_backends = None
    pagination_class = None
    permissions_map = {
        'get_authorization_link': (
            IsAuthenticated,
            IsAttorneyHasActiveSubscription,
            IsAttorneyHasNoConnectedAccount
        ),
        'process_auth_callback': (AllowAny,)
    }

    @action(methods=['GET'], detail=False, url_path='url')
    def get_authorization_link(self, request, *args, **kwargs):
        """API method to get `Express` account `authorization` url for attorney

        Returned url allows to register new `Express` account or authorize the
        existing one. Also it prepares `state_token` for a user to match it
        later in callback.

        Also this method raises `403` error in case if user with existing
        connected `account` tries to get a link for creation of a new one.

        """
        # serializer = SuccessErrorUrlRequestSerializer(data=request.query_params)  # noqa
        # serializer.is_valid(raise_exception=True)

        state = str(uuid.uuid4())
        auth_url = stripe_deposits_service.get_authorization_url(
            state=state, user=request.user
        )
        # remember random `state` to make further user match in Stripe auth
        # callback + remember `success_url` and `error_url` to which user
        # will be redirected on further auth steps
        # cache.set(
        #     state, {
        #         'user_id': request.user.id,
        #         'success_url': serializer.validated_data['success_url'],
        #         'error_url': serializer.validated_data['error_url']
        #     },
        #     60 * 60 * 24  # 1 day
        # )
        return response.Response(
            data=URLSerializer({'url': auth_url}).data,
            status=status.HTTP_200_OK
        )

    @action(methods=['GET'], detail=False, url_path='callback')
    def process_auth_callback(self, request, *args, **kwargs):
        """API method to handle Stripe connect OAuth redirect.

        This method processes returned `state` and `code`, exchanges it to
        created account id and access token, creates new stripe Account
        instance in DB and links it with `user` from cache params.

        """
        data = request.query_params
        success = 'error' not in data
        serializer = (
            SuccessCallbackSerializer(data=data) if success else
            ErrorCallbackSerializer(data=data)
        )
        is_valid = serializer.is_valid(raise_exception=False)

        state_info = cache.get(data.get('state'), {})
        error_return_url = state_info.get('error_url')
        success_return_url = state_info.get('success_url')
        user = AppUser.objects.filter(id=state_info.get('user_id')).first()

        # redirect to corresponding page if there is an error
        if not is_valid or not success or not state_info or not user:
            error_return_url = error_return_url or \
                settings.STRIPE_BASE_AUTH_ERROR_REDIRECT_URL
            return response.Response(
                headers={'Location': error_return_url},
                status=status.HTTP_302_FOUND
            )

        try:
            # not allow to create new account for user with existing one
            if user.finance_profile.deposit_account is not None:
                raise AttributeError(
                    f'User {user} already has deposit account'
                )

            # try to exchange returned code to auth `token`
            token_data = stripe_deposits_service.get_token(data['code'])
            # save connected account in DB and link it with user
            account = AccountProxy.get_connected_account_from_token(
                access_token=token_data['access_token']
            )
            user.finance_profile.deposit_account = account
            user.finance_profile.save()
            # do account resync to get actual data and notify user
            account = AccountProxy.resync(account.id)
            account.notify_user()

        # log warning only when user has no `finance_profile` or
        # `deposit account` already exists
        except (AttributeError, FinanceProfile.DoesNotExist) as e:
            return self._process_auth_callback_error(
                e, user, error_return_url, False
            )

        # log error when couldn't get `token` or `account` from stripe
        except Exception as e:
            return self._process_auth_callback_error(
                e, user, error_return_url, False
            )

        return response.Response(
            headers={'Location': success_return_url},
            status=status.HTTP_302_FOUND
        )

    def _process_auth_callback_error(
        self, error: Exception, user: AppUser, error_return_url: str,
        log_error=True,
    ) -> response.Response:
        """Handle errors appeared in `process_auth_callback` try/catch.

        Arguments:
            error (Exception): raised in try/catch block error
            error_return_url (str): error url to which user should be returned
            user (AppUser): user of the app for which callback is processed
            log_error (bool): flag which designates whether error should be
                logged as `error` or `warning`

        """
        log_method = logger.error if log_error else logger.warning
        log_method(
            f"Couldn't create connected account for user {user.id}: {error}"
        )
        return response.Response(
            headers={'Location': f'{error_return_url}?error={error}'},
            status=status.HTTP_302_FOUND
        )


class CurrentAccountViewSet(BaseViewSet):
    """Viewset to retrieve user's direct deposit account and its login link.
    """
    base_filter_backends = None
    pagination_class = None

    serializer_class = AccountProxySerializer
    permission_classes = IsAuthenticated, IsAttorneyHasActiveSubscription

    def get_object(self):
        """Overridden method to return user's account from `finance_profile`.
        """
        finance_profile = getattr(self.request.user, 'finance_profile', None)
        account = getattr(finance_profile, 'deposit_account', None)
        if not account:
            raise Http404
        return account

    @action(methods=['GET'], detail=False, url_path='current')
    def get_current(self, request, *args, **kwargs):
        """Custom method to get user's current account without `id` param.

        The same as original DRF `retrieve` implementation, but without `id`
        param in path.

        Stripe Docs: https://stripe.com/docs/api/accounts/object

        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return response.Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['GET'], detail=False, url_path='current/login-url')
    def get_login_link(self, request, *args, **kwargs):
        """API method to get login link to Express account dashboard in Stripe.

        Stripe docs: https://stripe.com/docs/connect/express-dashboard

        """
        account = self.get_object()
        return response.Response(
            data=URLSerializer({'url': account.login_url}).data,
            status=status.HTTP_200_OK
        )

    @action(methods=['GET'], detail=False, url_path='current/onboarding-url')
    def get_onboarding_link(self, request, *args, **kwargs):
        """API method to get onboarding link to Express account dashboard in Stripe.

        Stripe docs: https://stripe.com/docs/connect/express-dashboard

        """
        user = request.user
        account = stripe.Account.create(
            type='express',
            country='US',
            email=user.email,
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
        )
        if 'local' in os.environ.get('ENVIRONMENT', ''):
            current_site = config.LOCAL_FRONTEND_LINK
        elif 'development' in os.environ.get('ENVIRONMENT', ''):
            current_site = config.DEV_FRONTEND_LINK
        elif 'staging' in os.environ.get('ENVIRONMENT', ''):
            current_site = config.STAGING_FRONTEND_LINK
        elif 'prod' in os.environ.get('ENVIRONMENT', ''):
            current_site = config.PROD_FRONTEND_LINK
        else:
            current_site = ''
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=f"{current_site}attorney/bank",
            return_url=f"{current_site}attorney/bank",
            type="account_onboarding",
        )
        return response.Response(
            data=URLSerializer({'url': account_link.url}).data,
            status=status.HTTP_200_OK
        )
