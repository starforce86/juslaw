from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class BillingItemLimitOffsetPagination(LimitOffsetPagination):
    """Pagination to add billing item info to the pagination data.

    Provide additional info for selected billing item data, it could be
    accessed easily within single request from frontend. Other wise we should
    add

    """
    def __init__(self):
        self.total_fees = 0
        self.total_time = ''

    def paginate_queryset(self, queryset, request, view=None):
        """Collect total fees and total time from initial queryset.

        This is the only place to access initial queryset inside pagination.

        """
        self.total_fees = queryset.get_total_fee()
        self.total_time = queryset.get_total_time()
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data, **kwargs):
        """Provide custom response with time billing info."""
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('total_fees', self.total_fees),
            ('total_time', self.total_time),
        ]))
