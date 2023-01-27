from rest_framework.permissions import IsAuthenticated

from rest_condition import And, Or

from ....users.api.permissions import (
    IsAttorneyHasActiveSubscription,
    IsClient,
    IsParalegal,
    IsSupportPaidFee,
)


class BusinessViewSetMixin:
    """Mixin which combines similar logic of `business` app views

    All `business` app views have the same actions permissions:

        * `client` - can only list and retrieve instances where he is a client
        (or matter client).

        * `attorney` - can create, delete, list, retrieve and update instances
        where he is an attorney (or matter attorney) or if he is an attorney
        with which the matter was shared.

        * `support` - can create (not always), delete, list, retrieve and
        update instances which matter is shared with him.

    """
    attorney_permissions = (
        IsAuthenticated,
        IsAttorneyHasActiveSubscription,
    )
    client_permissions = (
        IsAuthenticated,
        IsClient,
    )
    attorney_support_permissions = Or(
        And(IsAuthenticated(), IsAttorneyHasActiveSubscription()),
        And(IsAuthenticated(), IsSupportPaidFee()),
    )
    support_permissions = Or(
        And(IsAuthenticated(), IsAttorneyHasActiveSubscription()),
        And(IsAuthenticated(), IsSupportPaidFee()),
        And(IsAuthenticated(), IsParalegal()),
    )
    permissions_map = {
        'create': (attorney_support_permissions,),
        'update': (attorney_support_permissions,),
        'partial_update': (attorney_support_permissions,),
        'destroy': (attorney_support_permissions,),
    }

    def get_queryset(self):
        """Filter all available for user instances

        Here are returned on instances, where current user is a client (if he
        is a client) or attorney (if he is attorney).

        """
        qs = super().get_queryset()
        order_param = self.request.query_params.get('ordering', None)
        if order_param == '' or order_param is None:
            return qs.available_for_user(self.request.user).order_by('id')
        return qs.available_for_user(self.request.user)
