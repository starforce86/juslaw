from django.db import models
from django.utils.translation import gettext_lazy as _

from ...finance.models import AbstractPaidObject, Payment
from .querysets import SupportQuerySet
from .users import AppUserHelperMixin
from .utils.verification import VerifiedRegistration


class Support(AbstractPaidObject, AppUserHelperMixin, VerifiedRegistration):
    """Model defines information about `support` attorneys users.

    Support users are a kind of attorney helper users, like:

        - paralegal - individuals who is employed or retained by attorney and
        who performs specifically delegated substantive legal work for which an
        attorney is responsible. Paralegals perform tasks requiring knowledge
        of the law and legal procedures. They are like attorney's assistants.

        - clerical - individuals who are attorney's assistants which perform
        more office and documents work, they are like attorney's secretaries.

        - etc.

    This kind of users have no possibility to use Django Admin, create own
    matters, participate in forum or leads and etc. The only available
    functionality is managing `shared with them` matters with its related
    information and managing their own profiles.

    Existing attorneys or clients can't become `support` users, this is a
    separately registered type of user, which pays some `fee` to become a
    `support` after admin's verification.

    Attributes:
        user (AppUser): Relation to AppUser
        description (str): Role description (like Paralegal, Admin, clerical)
        verification_status (str):
            Verification_status of support user, there three statuses:
                not_verified - Default on creation
                approved - Approved by admins
                denied - Denied by admins
        payment_status (str): Status of fee payment. Can be:
            * not_started - Payment is about to start or was canceled and
            will be restarted.
            * payment_in_progress - Fee payment is in progress
            * payment_failed - Fee payment attempt failed
            * paid - Fee paid
        payment (Payment): Link to fee payment
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """
    DISPLAY_NAME = 'Paralegal'

    user = models.OneToOneField(
        'users.AppUser',
        primary_key=True,
        on_delete=models.PROTECT,
        verbose_name=_('User'),
        related_name='support'
    )
    # TODO: @Kseniya find out who changes and sets `description` - admin or
    #  support user
    description = models.CharField(
        max_length=128,
        verbose_name=_('Description'),
        help_text=_("User's description (role)")
    )

    objects = SupportQuerySet.as_manager()

    class Meta:
        verbose_name = _('Paralegal')
        verbose_name_plural = _('Paralegal users')

    def can_pay(self, user) -> bool:
        """Return ``True`` if ``user`` can pay for access fee.

        Fee can be paid only by user itself and when it's user support profile
        is verified.

        """
        if not super().can_pay(user):
            return False
        return user.pk == self.pk and self.is_verified

    def _get_or_create_payment(self) -> Payment:
        """Create payment for fee."""
        from ..services import get_or_create_support_fee_payment
        return get_or_create_support_fee_payment(support=self)

    def _post_fail_payment_hook(self):
        """Notify user about failed payment."""
        from .. import notifications
        notifications.FeePaymentFailedNotification(paid_object=self).send()

    def _post_cancel_payment_hook(self):
        """Notify user about canceled payment."""
        from .. import notifications
        notifications.FeePaymentCanceledNotification(paid_object=self).send()

    def _post_finalize_payment_hook(self):
        """Notify user about successful payment"""
        from .. import notifications
        notifications.FeePaymentSucceededNotification(paid_object=self).send()
