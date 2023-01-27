from rest_framework.fields import CharField

from ....users import models


class AttorneyUniversityField(CharField):
    """Field that allows to use `University` by `title` in serializer."""

    def to_internal_value(self, title):
        """Transform data to `University` instance.

        If there are university with provided title, we return this university,
        otherwise we create new University with provided title.
        """
        title = super().to_internal_value(title)
        try:
            return models.AttorneyUniversity.objects.get(title__iexact=title)
        except models.AttorneyUniversity.DoesNotExist:
            return models.AttorneyUniversity(title=title)


class ParalegalUniversityField(CharField):
    """Field that allows to use `University` by `title` in serializer."""

    def to_internal_value(self, title):
        """Transform data to `University` instance.

        If there are university with provided title, we return this university,
        otherwise we create new University with provided title.
        """
        title = super().to_internal_value(title)
        try:
            return models.ParalegalUniversity.objects.get(title__iexact=title)
        except models.ParalegalUniversity.DoesNotExist:
            return models.ParalegalUniversity(title=title)
