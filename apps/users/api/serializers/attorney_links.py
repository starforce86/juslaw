from rest_framework import serializers

from ....core.api.serializers import BaseSerializer
from ....users import models
from .fields import AttorneyUniversityField


class AttorneyUniversitySerializer(BaseSerializer):
    """Serializer for `University` model."""

    class Meta:
        model = models.AttorneyUniversity
        fields = (
            'id', 'title'
        )


class AttorneyEducationSerializer(BaseSerializer):
    """Serializer for `AttorneyEducation` model."""
    university = AttorneyUniversityField()

    class Meta:
        model = models.AttorneyEducation
        fields = (
            'id',
            'year',
            'university',
        )

    def validate(self, attrs):
        """Save new `University` instance if data passed validation."""
        attrs = super().validate(attrs)
        if 'university' in attrs and not attrs['university'].pk:
            attrs['university'].save()
        return attrs


class UpdateAttorneyEducationSerializer(AttorneyEducationSerializer):
    """Exposes id field for `put` or `patch` method."""
    id = serializers.IntegerField()
