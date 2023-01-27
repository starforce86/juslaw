from drf_yasg import openapi
from drf_yasg.inspectors import DjangoRestResponsePagination

from apps.business.api.pagination import BillingItemLimitOffsetPagination


class BillingItemPaginationInspector(DjangoRestResponsePagination):
    """Pagination inspector to provide additional fields in spec.

    This inspector will add `total_fees` and `total_time` fields in
    response model of selected method with pagination.

    """
    def get_paginated_response(self, paginator, response_schema):
        """Update default paged_schema with time billing fields."""
        paged_schema = \
            super().get_paginated_response(paginator, response_schema)

        if isinstance(paginator, BillingItemLimitOffsetPagination):
            paged_schema.properties.update(
                {
                    'total_fees': openapi.Schema(
                        type=openapi.TYPE_NUMBER,
                        title='Sum of all selected fees (on all pages).',
                    ),
                    'total_time': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        title='Total billed time (on all pages).',
                    ),
                }
            )

        return paged_schema
