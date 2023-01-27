from django.utils.decorators import method_decorator

from drf_yasg.utils import swagger_auto_schema
from s3direct.api import views
from s3direct.api.serializers import S3DirectSerializer, S3UploadSerializer


@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        request_body=S3DirectSerializer,
        responses={200: S3UploadSerializer}
    )
)
class S3DirectWrapper(views.S3DirectWrapper):
    """Overridden to expand documentation(serializers)."""
