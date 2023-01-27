from django.conf import settings

from rest_framework import permissions


class IsAttorneyHasActiveSubscription(permissions.BasePermission):
    """Permission which checks that user has access to paid resources

    Applied to these endpoints:

        * `/api/v1/users/attorneys/current/ ` CurrentAttorneyView
        * `/users/attorneys/current/statistics/current/` StatisticsAttorneyView
        * `/api/v1/business/leads/` LeadViewSet
        * `/api/v1/business/matters/` MatterViewSet
        * `/api/v1/business/billing-items/` BillingItemViewSet
        * `/api/v1/promotion/events/` EventViewSet
        * `/api/v1/business/invoices/` InvoiceViewSet
        * `/api/v1/business/activities/` ActivityViewSet
        * `/api/v1/business/notes/` NoteViewSet
        * `/api/v1/business/checklist/` ChecklistEntryViewSet
        * `/api/v1/business/stages/` StageViewSet
        * `/api/v1/esign/envelopes/` EnvelopeViewSet
        * `/api/v1/esign/profiles/current/` CurrentESignProfileView
        * `/api/v1/accounting/auth/` QuickBooksAuthorizationView

    """
    def has_permission(self, request, view):
        """Check if subscription is valid and user is attorney"""
        if not request.user.is_attorney:
            return False
        # Skip subscription permission for development or local envs or
        # attorney is an old instance for testing
        if any([
            settings.ENVIRONMENT in ['local'] and not settings.STRIPE_ENABLED,
            not request.user.customer
        ]):
            return True
        return request.user.has_active_subscription


class IsAttorneyFreeAccess(permissions.BasePermission):
    """Permission which checks if request user is Attorney"""

    def has_permission(self, request, view):
        """Check if request user is Attorney"""
        return request.user.is_attorney


class IsParalegal(permissions.BasePermission):
    """Permission which checks if request user is Paralegal"""

    def has_permission(self, request, view):
        """Check if request user is Paralegal"""
        return request.user.is_paralegal


class IsEnterprise(permissions.BasePermission):
    """Permission which checks if request user is Enterprise"""

    def has_permission(self, request, view):
        """Check if request user is Enterprise"""
        return request.user.is_enterprise


class IsClient(permissions.BasePermission):
    """Permission which checks if request user is Client"""

    def has_permission(self, request, view):
        """Check if request user is Client"""
        return request.user.is_client


class IsSupport(permissions.BasePermission):
    """Permission which checks if request user is Support"""

    def has_permission(self, request, view):
        """Check if request user is Support"""
        return request.user.is_support


class CanUpdatePA(permissions.BasePermission):
    """Permission which checks if user can update PA list"""

    def has_permission(self, request, view):
        """Check if request user is Support"""
        return (
            request.user.is_staff or
            request.user.is_attorney or
            request.user.is_paralegal
        )


class IsSupportPaidFee(permissions.BasePermission):
    """Permission which checks that support user paid fee."""

    def has_permission(self, request, view):
        """Check if user is support and paid subscription fee."""
        if not request.user.is_support:
            return False

        # Skip subscription permission for  local envs
        if settings.ENVIRONMENT == 'local' and not settings.STRIPE_ENABLED:
            return True

        return request.user.support.is_paid


class CanFollow(permissions.IsAuthenticated):
    """Permission which checks is user allowed to follow attorney.

    Checks if user isn't trying to follow itself.
    Checks if user is client.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user isn't trying to follow itself and it's not attorney"""
        return request.user != obj.user and request.user.is_client


class IsInviteOwner(IsAttorneyFreeAccess):
    """Permission which checks if user is owner of invite."""

    def has_object_permission(self, request, view, obj):
        """Check if request user is owner of invite."""
        return obj.inviter == request.user
