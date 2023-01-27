from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class BusinessStatsQueryParamsSerializer(serializers.Serializer):
    """Serializer for validating params for business's statistics export."""
    period_start = serializers.DateField(
        required=True, help_text='Date format: `YYYY-MM-DD`'
    )
    period_end = serializers.DateField(
        required=True, help_text='Date format: `YYYY-MM-DD`'
    )
    extension = serializers.ChoiceField(
        choices=['csv', 'xls', 'xlsx'], default='xls'
    )

    def validate(self, attrs):
        """Validate `period_start` and `period_end` dates."""
        period_start = attrs['period_start']
        period_end = attrs['period_end']
        if period_start > period_end:
            raise ValidationError(
                "Enter valid 'period_start' and 'period_end' dates"
                "('period_start' is after 'period_end')"
            )
        return attrs
