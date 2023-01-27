from django.contrib.auth.base_user import BaseUserManager
from django.db.models import Q

from .querysets import AppUserQuerySet


class AppUserManager(BaseUserManager.from_queryset(AppUserQuerySet)):
    """Custom manager which doesn't use username."""

    def create_user(self, email, password, **extra_fields):
        """Create user, but without using username."""
        if not email:
            raise ValueError('Enter an email address')
        if not password:
            raise ValueError('Enter password')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **kwargs):
        """Create superuser without using username."""
        user = self.create_user(
            email,
            password=password,
            is_superuser=True,
            is_staff=True,
            **kwargs
        )
        return user

    def had_business_with(self, user):
        """Get all app users that user had some business with.

        For attorney:
            Had matter or lead with client.
            Invited user
        For client:
            Had matter or lead with attorney.
            Was invited by attorney

        """
        attorney_matter_filter = Q(client__matters__attorney_id=user.pk)
        attorney_client_lead_filter = Q(client__leads__attorney_id=user.pk)
        attorney_invite_filter = Q(invitations__inviter_id=user.pk)

        client_matter_filter = Q(attorney__matters__client_id=user.pk)
        client_client_lead_filter = Q(attorney__leads__client_id=user.pk)
        client_invite_filter = Q(sent_invitations__user_id=user.pk)

        return self.filter(
            attorney_matter_filter |
            attorney_client_lead_filter |
            attorney_invite_filter |
            client_matter_filter |
            client_client_lead_filter |
            client_invite_filter
        ).distinct()
