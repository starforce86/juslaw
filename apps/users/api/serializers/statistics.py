from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class TimeFrameStatisticsDataSerializer(serializers.Serializer):
    """Serializer to show statistics for time frame of time period.

    Created for swagger specs.

    """
    date = serializers.DateTimeField()
    count = serializers.IntegerField(min_value=0)


class PeriodStatisticsDataSerializer(serializers.Serializer):
    """Serializer to show statistics for of time period.

    Created for swagger specs.

    """
    total_sum = serializers.DateTimeField()
    stats = TimeFrameStatisticsDataSerializer(many=True)


class AttorneyPeriodStatisticsDataSerializer(serializers.Serializer):
    """Serializer to show attorney statistics for time period.

    Created for swagger specs.

    """
    time_billed = PeriodStatisticsDataSerializer()
    active_leads_stats = PeriodStatisticsDataSerializer()
    active_matters_stats = PeriodStatisticsDataSerializer()
    converted_leads_stats = PeriodStatisticsDataSerializer()


class AttorneyCurrentStatisticsDataSerializer(serializers.Serializer):
    """Serializer for current attorney's statistics."""
    opportunities_count = serializers.IntegerField(min_value=0)
    active_leads_count = serializers.IntegerField(min_value=0)
    active_matters_count = serializers.IntegerField(min_value=0)
    documents_count = serializers.IntegerField(min_value=0)


class AttorneyPeriodStatsQueryParamsSerializer(serializers.Serializer):
    """Serializer for validating params for attorney's statistics."""
    start = serializers.DateTimeField(required=True)
    end = serializers.DateTimeField(required=True)
    time_frame = serializers.ChoiceField(
        default='month',
        choices=(
            'year',
            'quarter',
            'month',
            'day',
        )
    )

    def validate(self, attrs):
        """Validate `start` and `end` dates."""
        start = attrs['start']
        end = attrs['end']
        if start > end:
            raise ValidationError(
                "Enter valid 'start' and 'end' dates"
                "('start' is after 'end')"
            )
        return attrs
