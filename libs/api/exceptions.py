import json

from django.core.exceptions import PermissionDenied as CorePermissionDenied
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions, status
from rest_framework.exceptions import (
    APIException,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.views import exception_handler

import inflection

from libs import utils


class CustomAPIException(APIException):
    """Custom exception for API.

    Allows to implement custom API error messages. Exception class must be
    inherited from ``CustomAPIException`` class and can override some of its
    arguments: status_code, code and message.

    If status_code attribute is not overriden - it's set to 500.
    If code attribute is not overriden - it's generated from class name.
    If message attribute is not overriden - it's set to default message.

    Args:
        code (str): code of the error.
        message (str): messae of the error.

    Example:
        class CustomCodeError(CustomAPIException):
            status_code = 404
            code = 'ABC123'
            message = 'This is custom error message.'

    """
    code = None
    message = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.code:
            self.default_code = self.code
        else:
            self.default_code = inflection.underscore(self.__class__.__name__)

        self.detail = _(self.message or self.detail)
        self.default_detail = self.detail


def custom_exception_handler_simple(exc, context):
    """Handle simple drf exceptions.

    This custom exception handler for django REST framework wraps
    ValidationErrors into field `data` and adds `detail` field with
    first non field error or message:
        Unfortunately, there are some problems with the data you committed

    """
    if isinstance(exc, exceptions.ValidationError):
        if 'non_field_errors' in exc.detail:
            exc.detail = {
                'data': exc.detail,
                'detail': exc.detail['non_field_errors'][0]
            }
        else:
            detail = list(exc.detail.values())[0][0]
            # detail_field = ' '.join([w.capitalize() for w in list(exc.detail.keys())[0].split('_')])
            exc.detail = {
                'data': exc.detail,
                # 'detail': detail_field + ': ' + detail
                'detail': detail
            }
    elif isinstance(exc, Http404):
        pass
    elif isinstance(exc, APIException):
        pass
    else:
        detail = str(exc)
        if utils.is_json(detail) and json.loads(detail).get('message'):
            detail = json.loads(detail).get('message')

        exc = ValidationError(detail={
            'detail': detail
        })

    return exception_handler(exc, context)


def custom_exception_handler(exc, context=None):
    """Handle exceptions for django REST framework.

    Handler wraps ValidationErrors into field `validation_errors` (for field
    errors) and adds `detail` and `code` fields.

    For non field errors `detail` message is:
        "Unfortunately, there are some problems with the data you committed"

    Args:
        exc (Exception): Instance of ``Exception`` (e.g. ValidationError)
        context (dict): context of the Exception

    Return:
        Response: response to the exception

    Example:
        # Non field errors:
        {
          "detail": "Unable to log in with provided credentials.",
          "code": "validation_errors"
        }

        # Field errors:
        {
          "code": "validation_error",
          "validation_errors": [{
              "errors": ["This password is too common.",],
              "field": "password1"
            }],
          "detail": "Unfortunately, there are some problems with the data
          you committed"
        }

    """
    validation_errors = []

    if isinstance(exc, CorePermissionDenied):
        exc = PermissionDenied()

    if isinstance(exc, Http404):
        exc = NotFound()

    if isinstance(exc, ValidationError):
        code = 'validation_error'
        detail = _(
            'Unfortunately, there are some problems '
            'with the data you committed'
        )

        if 'non_field_errors' in exc.detail:
            detail = exc.detail['non_field_errors'][0]
            exc.detail.pop('non_field_errors')

        if isinstance(exc.detail, list):
            detail = exc.detail[0]

        if isinstance(exc.detail, dict):
            for field, errors in exc.detail.items():
                validation_errors.append({
                    'field': field,
                    'errors': errors
                })
    elif isinstance(exc, APIException):
        code = exc.default_code
        detail = exc.detail
    else:
        # Unhandled Exceptions (e.g. AssertionError)
        return None
    # Exceptions, inherited from ``CustomAPIException`` already
    # have proper format of details section.

    exc.detail = {
        'detail': detail,
        'code': code,
    }

    if validation_errors:
        exc.detail.update({
            'validation_errors': validation_errors
        })

    return exception_handler(exc, context)


class ConflictError(APIException):
    """Used to return 409 response on errors."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Input conflicts with existing data.')
    default_code = 'conflict'
