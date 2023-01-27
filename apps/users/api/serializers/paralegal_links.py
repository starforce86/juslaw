from rest_framework import serializers

from ....core.api.serializers import BaseSerializer
from ....users import models
from .fields import ParalegalUniversityField


class ParalegalEducationSerializer(BaseSerializer):
    """Serializer for `ParalegalEducation` model."""
    university = ParalegalUniversityField()

    class Meta:
        model = models.ParalegalEducation
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


class UpdateParalegalEducationSerializer(ParalegalEducationSerializer):
    """Exposes id field for `put` or `patch` method."""
    id = serializers.IntegerField()
