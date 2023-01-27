from rest_framework import status
from rest_framework.exceptions import APIException


class WrongTransitionException(APIException):
    """This exception should be risen when you cannot perform status changing

    Examples:
        try:
            obj.activate()
            obj.save()
        except TransitionNotAllowed:
            raise WrongTransitionException
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Action is not allowed for current status'
