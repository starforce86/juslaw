from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException

__all__ = (
    'GetJWTTokenException',
    'GetAccessTokenException',
    'GetUserDataException',
    'CreateEnvelopeException',
    'UpdateEnvelopeException',
    'CreateEditEnvelopeViewException',
    'UserHasNoConsentException',
    'NoEnvelopeExistsException',
)


class GetJWTTokenException(APIException):
    """Custom exception to track errors with impersonalization."""
    default_detail = _("Couldn't impersonate user in DocuSign")


class GetAccessTokenException(APIException):
    """Custom exception to track errors with getting access token."""
    default_detail = _("Couldn't get access token for user from DocuSign")


class GetUserDataException(APIException):
    """Custom exception to track errors with getting user data."""
    default_detail = _("Couldn't get user data from DocuSign")


class CreateEnvelopeException(APIException):
    """Custom exception to track errors with creating envelope."""
    default_detail = _("Couldn't create Envelope in DocuSign")


class UpdateEnvelopeException(APIException):
    """Custom exception to track errors with updating envelope."""
    default_detail = _("Couldn't update Envelope in DocuSign")


class CreateEditEnvelopeViewException(APIException):
    """Custom exception to track errors with creating edit envelope view."""
    default_detail = _("Couldn't create edit view for Envelope in DocuSign")


class NoEnvelopeExistsException(APIException):
    """Custom exception to track errors when envelope doesn't exist anymore."""
    default_detail = _("Envelope doesn't exist in DocuSign")


class UserHasNoConsentException(APIException):
    """Custom exception to track errors when user has no consent."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User has no consent in DocuSign")
