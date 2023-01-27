from rest_framework import serializers

from ....core.api.serializers import BaseSerializer
from ... import models


class PaymentObjectDataSerializer(serializers.Serializer):
    """Serializer present payment object data for `Payment` model."""

    client_secret = serializers.CharField(allow_null=True)
    status = serializers.CharField()


class PaymentSerializer(BaseSerializer):
    """Serializer for `Payment` model."""

    payment_object_data = PaymentObjectDataSerializer()

    class Meta:
        model = models.Payment
        fields = (
            'id',
            'payer',
            'recipient',
            'amount',
            'application_fee_amount',
            'description',
            'status',
            'payment_object_data',
        )


class StartPaymentParamsSerializer(serializers.Serializer):
    """Serializer for model retrieval for payments."""

    object_type = serializers.ChoiceField(choices=(
        'invoice', 'support'
    ))
    object_id = serializers.IntegerField()
