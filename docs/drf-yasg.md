# Working with `drf-yasg`

## Use of `define_swagger_auto_schema`
If drf-yasg generates specs incorrectly or you want to customize it, you will need to use
`define_swagger_auto_schema` in `scheme.py` in `api` folder of app you working on.

You must pass `api_view` and `method`(`action`) for which you want customize `specs`.

```python
from apps.core.api.utils import define_swagger_auto_schema

define_swagger_auto_schema(
    api_view=APIView,
    method_name='update',
    # Add your params 
)
```

If you working on `new` app, then don't forget to add import of `scheme.py` file to 
the `app config`

```python
from django.apps import AppConfig


class UsersAppDefaultConfig(AppConfig):
    """Default configuration for Users app."""

    name = 'apps.users'
    verbose_name = 'Users'

    def ready(self):
        """Enable signals and schema definitions."""
        from . import signals  # noqa
        from .api import schema  # noqa
```

## Examples of `define_swagger_auto_schema` usage

If your api `action` doesn't require any input data you can set `response_body` to `no_body`(
`from drf_yasg.utils import no_body`)

```python
from drf_yasg.utils import no_body

from apps.core.api.utils import define_swagger_auto_schema

define_swagger_auto_schema(
    api_view=views.MatterViewSet,
    method_name='revoke',
    request_body=no_body,
)
```

To customize response specs, you need to `responses` param a `dict`  where must be a `status code`
(`int` or `str`) and the value response itself. Response can be a `Serializer` class, `str` if you 
don't return anything, but want to add some `explanation` and `None` if you want to ignore this 
response(it `won't appear` in specs)

```python
from apps.core.api.utils import define_swagger_auto_schema

define_swagger_auto_schema(
    api_view=views.ESignCallbacksView,
    method_name='save_consent',
    responses={
        '302': None,
        '400': 'Invalid data',
        '200': serializers.ESignProfileSerializer
    }
)
```

You want to add some params to your specs(for example for this endpoint `user/stats?stage=first`, 
you want to add `stage`), then you need to create `serializer` with all needed params and set it to
`query_serializer`.

```python
from apps.core.api.utils import define_swagger_auto_schema

class AttorneyRegisterValidateSerializer(serializers.Serializer):
    """Serializer to validate Attorney registration process"""
    stage = serializers.ChoiceField(choices=['first', 'second'], required=True)

define_swagger_auto_schema(
    api_view=views.AttorneyViewSet,
    method_name='validate_registration',
    query_serializer=serializers.AttorneyRegisterValidateSerializer,
)
```

You can also create your own `paginator inspectors` and use them in `define_swagger_auto_schema`.

```python
from apps.core.api.utils import define_swagger_auto_schema

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

define_swagger_auto_schema(
    api_view=views.BillingItemViewSet,
    method_name='list',
    paginator_inspectors=[BillingItemPaginationInspector]
)
```
