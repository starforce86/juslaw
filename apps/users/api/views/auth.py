import os

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.db.transaction import non_atomic_requests
from django.http.response import Http404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response

from allauth.account import app_settings
from allauth.account import views as account_views
from allauth.account.models import EmailAddress
from constance import config
from rest_auth import views
from rest_auth.registration import views as reg_views
from twilio.rest import Client

from apps.users.models.users import AppUser

from ...api import serializers
from .utils.verification import resend_email_confirmation


@method_decorator(non_atomic_requests, name='dispatch')
class AppUserLoginView(views.LoginView):
    """Authorisation endpoint.

    Default `LoginView` sends `user_logged_in` signal only when
    `REST_SESSION_LOGIN == True` (which enables session login in Login DRF API
    view), but there are issues with CSRF protection when this setting is set.

    So this setting is turned off and `user_logged_in` signal is sent in custom
    `AppUserLoginView` to set user `last_login`.

    Non-atomic transactions allow to save failed login attempts. Failed login
    attempts return `HTTP 400`, and Atomic transactions not allow to save
    data after errors.

    """
    serializer_class = serializers.AppUserLoginSerializer

    def login(self):
        """Send signal `user_logged_in` on API login."""
        super().login()

        user_logged_in.send(
            sender=self.user.__class__,
            request=self.request,
            user=self.user
        )

    def post(self, *args, **kwargs):
        """Authorization endpoint.

        On successful authentication returns token(
            `key`,
            `user_type`,
            `user_id`,
            `plan_id`
        ).

        """
        try:
            return super().post(*args, **kwargs)
        except EmailAddress.DoesNotExist:
            message = "The email you entered isn’t connected to an account"
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={
                    "success": False,
                    "message": message
                }
            )
        except NotAuthenticated:
            msg = (
                'You will be able to login after'
                ' your application gets approved'
            )
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "success": False,
                    "message": msg
                }
            )


class ValidateCredentialView(views.LoginView):
    serializer_class = serializers.AppUserLoginValidationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data['user'] is not None:
            return Response(
                status=status.HTTP_200_OK,
                data={'success': True}
            )
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'success': False,
                    'detail': 'User does not exist with these credentials'
                }
            )


class LogoutView(views.LogoutView):
    """Logout user from app.

    Accepts only post request. Returns the success message.
    """
    http_method_names = ('post',)


class PasswordChangeView(views.PasswordChangeView):
    """Change user's password.

    Accepts the following POST parameters:
        old_password
        new_password1
        new_password2
    Returns the success/fail message.

    """


class PasswordResetView(views.PasswordResetView):
    """Reset user's password.

    This endpoint send to user with url for resetting password, at the end of
    which is data for resetting the password.
    Example `1-5b2-e2c1ce64d63673f0e78f`, where:
        `1` - is `uid` or user id
        `5b2-e2c1ce64d63673f0e78f` - `token` for resetting password

    """


class PasswordResetConfirmView(views.PasswordResetConfirmView):
    """Change user's password on reset.

    This endpoint confirms the reset of user's password.

    Explanation of token and uid
    Example `1-5b2-e2c1ce64d63673f0e78f`, where:
        `1` - is `uid` or user id
        `5b2-e2c1ce64d63673f0e78f` - `token` for resetting password

    """


class VerifyEmailView(reg_views.VerifyEmailView):
    """Verify user's email address

    This endpoint verify email address with `key` of verification link

    """


class VerifyConfirmEmailRedirectView(account_views.ConfirmEmailView):
    """Redirect to email verification fail page"""
    if 'local' in os.environ.get('ENVIRONMENT', ''):
        url = config.LOCAL_FRONTEND_LINK
    elif 'development' in os.environ.get('ENVIRONMENT', ''):
        url = config.DEV_FRONTEND_LINK
    elif 'staging' in os.environ.get('ENVIRONMENT', ''):
        url = config.STAGING_FRONTEND_LINK
    elif 'prod' in os.environ.get('ENVIRONMENT', ''):
        url = config.PROD_FRONTEND_LINK
    else:
        url = ''

    def get_redirect_url(self):
        return self.url + 'auth/email-verified?success=true'

    def get(self, *args, **kwargs):
        try:
            self.object = self.get_object()
            if app_settings.CONFIRM_EMAIL_ON_GET:
                return self.post(*args, **kwargs)
        except Http404:
            self.object = None
        return redirect(
            self.url + 'auth/email-verified?success=false'
        )


class ResendEmailConfirmation(views.APIView):

    """Resend email verfication link to user"""

    def post(self, request):
        try:
            email = request.data['email']
            user = AppUser.objects.get(email__iexact=email)
            resend_email_confirmation(request, user, True)
            return Response(
                status=status.HTTP_200_OK,
                data={
                    "detail": "Resend verification successfully"
                }
            )
        except Exception:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "detail": "Not resend verification successfully"
                }
            )


class VerifyCodeView(views.APIView):

    """Verify Code for Two FA authentication"""

    def post(self, request):
        try:
            phone = request.data['phone']
            code = request.data['code']
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            service = settings.TWILIO_SERVICE
            client = Client(account_sid, auth_token)

            verification_check = client.verify.services(service)\
                .verification_checks.create(to=phone, code=code)
            return Response(
                status=status.HTTP_200_OK,
                data={
                    "success": verification_check.valid
                }
            )
        except Exception:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "success": False
                }
            )


class SyncPlanView(views.APIView):

    def get(self, request):
        from django.core import management
        management.call_command('djstripe_sync_plans_from_stripe', verbosity=0)
        return Response(
            status=status.HTTP_200_OK,
            data={
                "detail": "Sync plan successfully!"
            }
        )
