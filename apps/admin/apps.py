from django.contrib import admin
from django.contrib.admin.apps import AdminConfig as DjangoAdminConfig


class AdminConfig(DjangoAdminConfig):
    """Define custom admin app."""
    default_site = 'apps.admin.site.AdminSite'

    def ready(self):
        """Remove not needed admin panels.

        Also re-define fcm admin.

        """
        super().ready()
        # Import here, when admin app is ready
        from django.contrib.auth.models import Group

        from rest_framework.authtoken.models import Token

        from allauth.account.models import EmailAddress
        from allauth.socialaccount.models import (
            SocialAccount,
            SocialApp,
            SocialToken,
        )
        from taggit.models import Tag

        # Import to redefine admin panels
        from ..utils.celery_beat import admin as celery_beat_admin  # noqa
        from ..utils.fcm import admin as fcm_admin  # noqa

        admin_panes_to_remove = (
            EmailAddress,
            Token,
            Group,
            Tag,
            SocialAccount,
            SocialApp,
            SocialToken
        )
        for model in admin_panes_to_remove:
            try:
                admin.site.unregister(model)
            except admin.sites.NotRegistered:
                pass
