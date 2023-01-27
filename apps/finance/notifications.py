from abc import ABC, abstractmethod
from typing import List

from libs.notifications import email

__all__ = (
    'StripeAccountNotVerifiedEmailNotification',
    'StripeAccountVerifiedEmailNotification',
    'BasePaymentNotification',
    'StripeAccountVerifiedEmailNotification',
    'StripeAccountNotVerifiedEmailNotification',
)


class BaseStripeAccountEmailNotification(email.DefaultEmailNotification):
    """Base class with common logic for stripe account notification."""

    def __init__(self, stripe_account_url: str, recipients: List[str]):
        """Remember notification params.

        Arguments:
            stripe_account_url (str): url to user connected account in Stripe
            recipients (List[str]): list of recipients emails

        """
        super().__init__(recipient_list=recipients)
        self.stripe_account_url = stripe_account_url

    def get_template_context(self):
        """Return notification template context."""
        return {
            'stripe_account_url': self.stripe_account_url,
        }


class StripeAccountNotVerifiedEmailNotification(
    BaseStripeAccountEmailNotification
):
    """Email user when his Stripe account for direct deposits not verified."""

    template = 'finance/email/not_verified_account_notification.html'

    def get_subject(self):
        """Get email subject."""
        return 'Direct deposit account requires extra information'


class StripeAccountVerifiedEmailNotification(
    BaseStripeAccountEmailNotification
):
    """Email user when his Stripe account for direct deposits is verified."""

    template = 'finance/email/verified_account_notification.html'

    def get_subject(self):
        """Get email subject."""
        return 'Direct deposit account is verified'


class BasePaymentNotification(email.DefaultEmailNotification, ABC):
    """Used to send notifications about user's payments."""
    paid_object_name = None

    def __init__(self, paid_object, **template_context):
        """Init BaseFeePaymentNotification."""
        self.paid_object = paid_object
        super().__init__(
            recipient_list=self.get_recipient_list(),
            **template_context,
        )

    @abstractmethod
    def get_recipient_list(self):
        """Get paid object's payer email."""

    @abstractmethod
    def deep_link(self) -> str:
        """Get frontend deep link."""

    def get_template_context(self):
        """Add paid object and it's deep link to email context."""
        context = super().get_template_context()
        context[self.paid_object_name] = self.paid_object
        context['deep_link'] = self.deep_link
        return context
