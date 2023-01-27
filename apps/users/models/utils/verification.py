from django.db import models
from django.utils.translation import gettext_lazy as _

from django_fsm import FSMField, transition

from apps.core.models import BaseModel

from ... import notifications


class VerifiedRegistrationQuerySet(models.QuerySet):
    """Queryset class for `VerifiedRegistration` model."""

    def verified(self):
        """Get verified instances only."""
        return self.filter(
            verification_status=VerifiedRegistration.VERIFICATION_APPROVED
        )


class VerifiedRegistration(BaseModel):
    """Abstract model for `admin` verification functionality.

    Model adds `verification_status` field with its related business logic and
    helper methods and may be used for different `user-like` models (Attorneys,
    Support users and etc).

    It implements following registration verification workflow:

        1. Whenever new user is registered - mark him as `inactive` and send
        special `notification` to platform admins so they could review new
        user. User is not able to login to the system until he would be
        verified by platform admins.

        2. When admin marks user as `verified` -> user's `verification_status`
        is updated to `approved`, user becomes active and can login in app.
        Also user gets `email` notification that he was verified.

        3. When admin marks user as `not verified` -> user's
        `verification_status` is updated to `denied`, user becomes inactive
        and can't login in app. Also user gets `email` notification that his
        verification was declined.

    """
    VERIFICATION_NOT_VERIFIED = 'not_verified'
    VERIFICATION_APPROVED = 'approved'
    VERIFICATION_DENIED = 'denied'

    VERIFICATION_STATUSES = (
        (VERIFICATION_NOT_VERIFIED, _('Not verified')),
        (VERIFICATION_APPROVED, _('Approved')),
        (VERIFICATION_DENIED, _('Denied')),
    )

    verification_status = FSMField(
        max_length=20,
        choices=VERIFICATION_STATUSES,
        default=VERIFICATION_NOT_VERIFIED,
        verbose_name=_('Verification_status')
    )

    objects = VerifiedRegistrationQuerySet.as_manager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        """Check that all required data is set."""
        super().__init__(*args, **kwargs)
        assert self._meta.get_field('user')

    @property
    def is_verified(self):
        """Designate whether model instance is verified by admins."""
        return self.verification_status == self.VERIFICATION_APPROVED

    def register_new_user(self):
        """Register new user and notify admins."""
        self.user.is_active = False
        self.user.save()
        notifications.RegisterUserNotification(self.user).send()

    # special `high-level` methods that should be called to `approve` or
    # `deny` user's verification

    def verify_by_admin(self, **kwargs):
        """Approve user verification by admin."""
        self.verify(**kwargs)
        self.save()
        notifications.VerificationApprovedEmailNotification(self.user).send()

        # call special hook to process custom instance verification logic
        self.post_verify_by_admin_hook(**kwargs)

    def decline_by_admin(self, **kwargs):
        """Decline user verification by admin."""
        self.decline()
        self.save()
        notifications.VerificationDeclinedEmailNotification(self.user).send()

        # call special hook to process custom instance verification logic
        self.post_decline_by_admin_hook(**kwargs)

    # transitions to move instance from one status to another

    @transition(
        field=verification_status,
        source='*',
        target=VERIFICATION_APPROVED,
    )
    def verify(self, **kwargs):
        """Approve user instance verification.

        * Change verification status
        * Update user `is_active`

        """
        self.user.is_active = True
        self.user.save()

        # call special hook to process custom instance verification logic
        # No need to create initial subscription
        # After approval, user should be pass into onboarding process
        # including creating subsription
        # self.post_verify_hook(**kwargs)

    @transition(
        field=verification_status,
        source='*',
        target=VERIFICATION_DENIED
    )
    def decline(self, **kwargs):
        """Decline user instance verification.

        * Change verification status
        * Update user `is_active`

        """
        self.user.is_active = False
        self.user.save()

        # call special hook to process custom instance verification logic
        # No need to create initial subscription
        # After approval, user should be pass into onboarding process
        # including creating subsription
        # self.post_decline_hook(**kwargs)

    # hooks for adding custom logic during `verification` flow

    def post_verify_hook(self, **kwargs):
        """Separate hook to add custom `verification` business logic."""
        pass

    def post_decline_hook(self, **kwargs):
        """Separate hook to add custom `verification` business logic."""
        pass

    def post_verify_by_admin_hook(self, **kwargs):
        """Separate hook to add custom `verification` business logic."""
        pass

    def post_decline_by_admin_hook(self, **kwargs):
        """Separate hook to add custom `verification` business logic."""
        pass
