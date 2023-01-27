import copy

from django.db.models import QuerySet

from rest_framework.fields import ListField

from s3direct.api.fields import S3DirectUploadURLField


class S3DirectUploadURLListField(ListField):
    """Field that allows to show list of files as urls."""
    child = S3DirectUploadURLField()

    def __init__(self, attr_path, *args, **kwargs):
        """Same as original, but we set our own child attr."""
        super().__init__(*args, **kwargs)
        self.child = copy.deepcopy(self.child)
        self.attr_path = attr_path

    def to_representation(self, data: QuerySet):
        """Convert list of files to list of urls."""
        return [
            self.child.to_representation(getattr(item, self.attr_path))
            if item is not None else None
            for item in data.all()
        ]
