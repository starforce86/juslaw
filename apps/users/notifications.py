from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from constance import config

from libs.notifications.email import DefaultEmailNotification
from libs.utils import get_base_url

from ..finance.notifications import BasePaymentNotification
from ..users import models

# TODO: Improve it when constance will support pytest
# https://github.com/jazzband/django-constance/pull/338
ADMINS_EMAILS = config.ADMINS
MAINTAINERS_EMAILS = config.MAINTAINERS
if settings.TESTING:
    ADMINS_EMAILS = ['root@root.com']
    MAINTAINERS_EMAILS = ['root@root.com']


class AdminsEmailNotification(DefaultEmailNotification):
    """Used to send mails to admins."""
    recipient_list = ADMINS_EMAILS


class ManagersEmailNotification(DefaultEmailNotification):
    """Used to send mails to managers."""
    recipient_list = MAINTAINERS_EMAILS


class UserEmailNotification(DefaultEmailNotification):
    """Base class represent interface for send emails to user

    Instance user must have email attribute

    """
    def __init__(self, user):
        super().__init__(recipient_list=(user.email,))
        self.user = user

    def get_template_context(self):
        """Return notification template context."""
        return {
            'app_user': self.user,
            'user_type': self.user.user_type_display,
            'current_site': get_base_url(),
            'user_key': self.user.uuid,
        }

    def send(self) -> bool:
        self.is_subscribed = self.user.is_subscribed
        super().send()


class VerificationApprovedEmailNotification(UserEmailNotification):
    """Used to notify attorneys/support users when profile is approved by admin
    """
    template = 'users/email/verification/email_user_verified.html'

    def get_subject(self):
        """Get email subject."""
        return _('Congratulations! Your application has been approved.')

    def get_template_context(self) -> dict:
        """Add base_url to the context."""
        context = super().get_template_context()
        context['login_url'] = get_base_url()
        return context


class VerificationDeclinedEmailNotification(UserEmailNotification):
    """Used for notify attorneys/support users when profile is denied by admin.
    """
    template = (
        'users/email/verification/email_user_verification_declined.html'
    )

    def get_subject(self):
        """Get email subject."""
        return _(' Verification Declined')


class RegisterUserNotification(AdminsEmailNotification):
    """Used to notify admins about new registered attorneys/support users."""
    template = (
        'users/email/verification/email_new_user_needs_verification.html'
    )

    def __init__(self, user):
        super().__init__()
        self.user = user

    def get_subject(self):
        """Get email subject."""
        return _(
            f'New {self.user.user_type_display} is awaiting verification'
        )

    def get_template_context(self):
        """Return notification template context."""
        user_type = self.user.user_type
        if user_type == "other":
            user_type = "paralegal"
        link_to_admin = reverse_lazy(
            f'admin:users_{user_type}_change',
            # attorneys and support users have the same pk as its related users
            kwargs={
                'object_id': self.user.pk
            }
        )
        return {
            'app_user': self.user,
            'user_type': self.user.user_type_display,
            'link': f'{settings.BASE_URL}{link_to_admin}'
        }


class InviteNotification(DefaultEmailNotification):
    """Used to send invitation to attorney's client."""
    template = 'users/email/invite/email_invitation.html'

    def __init__(self, invite):
        """Set invite instance and recipient to clients email."""
        super().__init__(recipient_list=(invite.email,))
        self.invite = invite

    def get_subject(self):
        return f'You have been invited by {self.invite.inviter}'

    def get_template_context(self):
        """Return notification template context."""
        return {
            'invite': self.invite,
            'invite_link': self.prepare_invitation_link()
        }

    def prepare_invitation_link(self) -> str:
        """Prepare invitation link for front-end part."""
        if self.invite.user_type == models.Invite.USER_TYPE_CLIENT or \
                self.invite.user_type == models.Invite.USER_TYPE_LEAD:
            return config.CLIENT_INVITE_REDIRECT_LINK.format(
                domain=get_base_url(), invite=self.invite.uuid
            )
        elif self.invite.user_type == models.Invite.USER_TYPE_PARALEGAL:
            return config.PARALEGAL_INVITE_REDIRECT_LINK.format(
                domain=get_base_url(), invite=self.invite.uuid
            )
        else:
            return config.ATTORNEY_INVITE_REDIRECT_LINK.format(
                domain=get_base_url(), invite=self.invite.uuid
            )


class RegisteredClientNotification(DefaultEmailNotification):
    """Used to send email about registered client to attorney."""
    template = 'users/email/invite/email_invited_client_registered.html'

    def __init__(self, invite):
        """Set invite instance and recipient to clients email."""
        super().__init__(recipient_list=(invite.inviter.email,))
        self.invite = invite

    def get_subject(self):
        return f'{self.invite.user.full_name} Has Registered'

    def get_template_context(self):
        """Return notification template context."""
        return {
            'invite': self.invite,
        }


class BaseFeePaymentNotification(BasePaymentNotification):
    """Used to send notifications about support fee payments."""
    paid_object_name = 'support'

    def get_recipient_list(self):
        """Support user's email."""
        return [self.paid_object.email]

    @property
    def deep_link(self) -> str:
        """Get base frontend link and redirect user to dashboard."""
        return f'{get_base_url()}'


class FeePaymentSucceededNotification(BaseFeePaymentNotification):
    """Used to send notification that fee payment for support succeeded."""
    template = 'users/email/support/fee_payment_succeeded.html'
    subject = 'Fee Payment for paralegal user access paid'


class FeePaymentFailedNotification(BaseFeePaymentNotification):
    """Used to send notification that fee payment for support failed."""
    template = 'users/email/support/fee_payment_failed.html'
    subject = 'Fee Payment for paralegal user access failed'


class FeePaymentCanceledNotification(BaseFeePaymentNotification):
    """Used to send notification that fee payment for support was canceled."""
    template = 'users/email/support/fee_payment_canceled.html'
    subject = 'Fee Payment for paralegal user access canceled'


class EnterpriseMemberInvitationNotification(DefaultEmailNotification):
    """Used to send invitation email to memebers of enterprise"""
    template = 'users/email/invite/email_invitation.html'

    def __init__(self, member, enterprise):
        """Set invite instance and recipient to member email."""
        super().__init__(recipient_list=(member.email,))
        self.member = member
        self.enterprise = enterprise

    def get_subject(self):
        return f'You have been invited by {self.enterprise}'

    def get_template_context(self):
        """Return notification template context."""
        return {
            'invite_link': self.prepare_invitation_link()
        }

    def prepare_invitation_link(self) -> str:
        """Prepare invitation link for front-end part."""
        if self.member.type == models.Member.USER_TYPE_PARALEGAL:
            return config.PARALEGAL_INVITE_REDIRECT_LINK.format(
                domain=get_base_url(),
                invite=self.member.pk
            )
        return config.ATTORNEY_INVITE_REDIRECT_LINK.format(
            domain=get_base_url(),
            invite=self.member.pk
        )
