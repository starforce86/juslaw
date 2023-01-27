from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException


class AuthError(APIException):
    """Raised when we can't authenticate in QB."""


class RefreshTokenExpired(AuthError):
    """Raised when QB refreshed token is expired."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Refresh token is expired')


class NotAuthorized(AuthError):
    """Raised when QB client has no authorization params."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Not authenticated in QuickBooks')


class ObjectNotFound(APIException):
    """Raised when requested `object` is not found in QB."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Object is not found in QuickBooks')


class SaveObjectError(APIException):
    """Raised when `object` can't be saved in QB for some reasons."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Object can\'t be saved')


class DuplicatedObjectError(APIException):
    """Raised when `object` can't be saved in QB because of duplication."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Object is duplicated')
