from django.utils import timezone

from rest_framework import serializers

__all__ = (
    'LocationSerializer',
    'UploadSerializer',
    'URLSerializer',
    'SuccessErrorUrlRequestSerializer',
)


class URLSerializer(serializers.Serializer):
    """Simple serializer which returns `url` field."""
    url = serializers.URLField(required=False)


class UploadSerializer(serializers.Serializer):
    """Serializer for Image upload."""
    upload = serializers.ImageField(required=True)


class SuccessErrorUrlRequestSerializer(serializers.Serializer):
    """Simple serializer which gets `success` and `error` urls fields."""
    success_url = serializers.URLField(required=True)
    error_url = serializers.URLField(required=True)


class LocationSerializer(serializers.Serializer):
    """Location serializer.

    For use with GeoDjango model.

    """
    lat = serializers.DecimalField(max_digits=10, decimal_places=6,
                                   required=True)
    lon = serializers.DecimalField(max_digits=10, decimal_places=6,
                                   required=True)

    def to_representation(self, obj):
        """Convert cords in json format."""
        lon, lat = obj.coords
        return {
            'lon': lon,
            'lat': lat
        }

    def to_internal_value(self, data):
        """Convert data in python types."""
        try:
            self.lon = data['lon']
            self.lat = data['lat']
            return 'POINT({0} {1})'.format(data['lon'], data['lat'])
        except KeyError:
            return super().to_internal_value(data)

    def save(self, user=None):
        """Update user instance with valid data."""
        if user:
            user.location = self.validated_data
            user.location_updated = timezone.now()
            user.save()
        return user
