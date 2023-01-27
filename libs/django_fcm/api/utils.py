import functools

from django.core.exceptions import ImproperlyConfigured, ValidationError

from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from django_fsm import TransitionNotAllowed, has_transition_perm

from ..exceptions import TransitionFailedException
from .exceptions import WrongTransitionException


def transition_method(method_name):
    """Replace decorated method with method, which performs transition the
    of object from one status to another.

    Args:
        method_name (str): name of model's transition method

    Returns:
        function: decorator

    """

    def method_decorator(method):
        """Throw away method and returns new method to perform transition

        Args:
            method (function): empty method to decorate

        Returns:
            function: transition method
        """

        @functools.wraps(method)
        def api_method(self: GenericViewSet, *args, **kwargs):
            """Method for changing object's status using django-fsm

            Raises:
                WrongTransitionException: when transition is not allowed

            Returns:
                Response: serialized object and status HTTP 200

            """
            if not self.transition_result_serializer_class:
                raise ImproperlyConfigured(
                    f'Set transition_result_serializer_class in '
                    f'{self.__class__}'
                )
            transition_object = self.get_object()

            transition = getattr(transition_object, method_name)
            # check if current user has permissions for a transition
            try:
                if not has_transition_perm(transition, self.request.user):
                    raise exceptions.PermissionDenied
            except ValidationError as permission_error:
                raise exceptions.ValidationError(permission_error.message_dict)

            # Get parameters for transition
            transition_parameters = {'user': self.request.user}
            serializer_class = self.get_serializer_class()
            if serializer_class:
                context = self.get_serializer_context()
                transition_parameters.update(get_transition_parameters(
                    data=self.request.data,
                    serializer_class=serializer_class,
                    context=context,
                ))

            try:
                transition(**transition_parameters)
                transition_object.save()
            except TransitionFailedException:
                # Save on_error state
                transition_object.save()
                return Response(
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            except TransitionNotAllowed:
                raise WrongTransitionException

            serializer = self.transition_result_serializer_class(
                transition_object, context=self.get_serializer_context()
            )
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        return api_method

    return method_decorator


def get_transition_parameters(data: dict, serializer_class, context) -> dict:
    """Get transition parameters from request data."""
    transition_serializer = serializer_class(
        data=data,
        context=context,
    )
    transition_serializer.is_valid(raise_exception=True)
    return transition_serializer.validated_data
