import os

from allauth.account import forms
from allauth.account.adapter import get_adapter
from constance import config


class ResetPasswordForm(forms.ResetPasswordForm):
    """ResetPasswordForm is used by `AppUserPasswordResetConfirmSerializer`.

    Overridden to return link to front end-part and user id as int."""

    def save(self, request, **kwargs):
        """Overridden to return link to front end-part and user id as int."""
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
        email = self.cleaned_data["email"]
        token_generator = kwargs.get(
            "token_generator", forms.default_token_generator
        )

        for user in self.users:
            temp_key = token_generator.make_token(user)

            # send the password reset email
            url = config.PASSWORD_RESET_REDIRECT_LINK.format(
                domain=current_site, user_id=user.pk, token=temp_key
            )

            context = {
                "current_site": current_site,
                "username": user.first_name,
                "useremail": user.email,
                "password_reset_url": url,
                "request": request
            }

            get_adapter(request).send_mail(
                'account/email/password_reset_key',
                email,
                context
            )
        return self.cleaned_data["email"]
