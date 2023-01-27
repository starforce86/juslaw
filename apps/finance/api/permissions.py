from rest_framework import permissions

from ..models import Payment


class IsAttorneyHasNoConnectedAccount(permissions.BasePermission):
    """Permission which checks that user has no `connected` account yet."""

    def has_permission(self, request, view):
        """Check that user has no `connected` account for direct deposits yet.
        """
        user = request.user
        if not hasattr(user, 'finance_profile'):
            return False
        return user.finance_profile.deposit_account is None


class IsPaymentPayerPermission(permissions.BasePermission):
    """Permission which checks that user has started request's payment."""

    def has_object_permission(self, request, view, obj: Payment):
        """
        Return `True` if user is payer.
        """
        return obj.payer_id == request.user.pk
