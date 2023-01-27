import os

from django.http import HttpResponseRedirect
from django.urls import reverse

from allauth.account.adapter import DefaultAccountAdapter
from constance import config

from apps.users.models import AppUser


class AccountAdapter(DefaultAccountAdapter):
    """Adapter to store additional fields on registration.

    Adjust it if you need custom fields saved during user registration call
    http://django-allauth.readthedocs.org/en/latest/advanced.html#creating-and-populating-user-instances

    """

    def save_user(self, request, user, form, **kwargs):
        """Persist user.

        Args:
            user (users.AppUser): empty AppUser instance
            form (CustomRegisterSerializer): Serializer filled with values

        """
        user.avatar = form.cleaned_data.get('avatar', '')
        user.phone = form.cleaned_data.get('phone', None)
        return super().save_user(request, user, form)

    def respond_email_verification_sent(self, request, user):
        return HttpResponseRedirect(
            reverse("v1:account_email_verification_sent")
        )

    def format_email_subject(self, subject):
        return subject

    def send_confirmation_mail(self, request, emailconfirmation, signup):
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
        activate_url = self.get_email_confirmation_url(
            request,
            emailconfirmation)
        user = AppUser.objects.get(email=emailconfirmation.email_address.email)
        ctx = {
            "user": emailconfirmation.email_address.user,
            "is_client": user.is_client,
            "activate_url": activate_url,
            "current_site": current_site,
            "key": emailconfirmation.key,
            "user_key": emailconfirmation.email_address.user.uuid,
        }
        if signup:
            email_template = 'account/email/email_confirmation_signup'
        else:
            email_template = 'account/email/email_confirmation'
        if emailconfirmation.email_address.user.is_subscribed:
            self.send_mail(
                email_template,
                emailconfirmation.email_address.email,
                ctx
            )
