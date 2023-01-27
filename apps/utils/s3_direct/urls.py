from django.urls import re_path

from .views import S3DirectWrapper

urlpatterns = [
    re_path(
        r'^get_params/$',
        S3DirectWrapper.as_view(),
        name='get_s3_upload_params'
    ),
]
