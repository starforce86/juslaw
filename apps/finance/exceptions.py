from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException


class PaymentProfileCreationError(Exception):
    """Raises when creation payment data fail"""
    def __init__(self, message) -> None:
        self.message = message


class DefinitionPlanTypeError(APIException):
    """Raised when subscription plan doesn't have a type value"""
    default_detail = _("Unknown subscription plan type")


class InvalidSubscriptionAction(APIException):
    """Raised when there is an attempt to change an inactive subscription"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("You cannot change an inactive subscription")


class SubscriptionCreationError(APIException):
    """Raised when the user has invalid data to create a subscription"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Failed to create subscription.")
