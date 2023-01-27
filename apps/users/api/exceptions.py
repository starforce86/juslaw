from rest_framework import status
from rest_framework.exceptions import APIException


class AttorneySubscriptionError(APIException):
    """Represent errors with creation stripe subscription attorney"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Action is not allowed for current status'
