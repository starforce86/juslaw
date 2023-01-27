from typing import Union

from rest_framework import serializers

from djstripe.models import BankAccount, Card
from drf_yasg.utils import swagger_serializer_method

from ...models import AccountProxy


class SuccessCallbackSerializer(serializers.Serializer):
    """Serializer to represent successful auth callback from Stripe connect."""
    code = serializers.CharField(required=True)
    state = serializers.CharField(required=True)


class ErrorCallbackSerializer(serializers.Serializer):
    """Serializer to represent error auth callback from Stripe connect."""
    error = serializers.CharField(required=True)
    error_description = serializers.CharField(required=True)
    state = serializers.CharField(required=True)


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer for djstripe `BankAccount` model (for swagger spec only).

    This serializer is used to represent Account `external_accounts`.

    """

    class Meta:
        model = BankAccount
        fields = '__all__'


class CardSerializer(serializers.ModelSerializer):
    """Serializer for djstripe `Card` model (for swagger spec only).

    This serializer is used to represent Account `external_accounts`.

    """

    class Meta:
        model = Card
        fields = '__all__'


class AccountProxySerializer(serializers.ModelSerializer):
    """Serializer for `AccountProxy` model."""

    capabilities = serializers.JSONField(
        source='info.capabilities',
        read_only=True
    )
    # split original model `external_accounts` to 2 fields
    bank_external_account = serializers.SerializerMethodField()
    card_external_account = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = AccountProxy
        fields = (
            'id',
            'charges_enabled',
            'payouts_enabled',
            'requirements',
            'capabilities',
            'bank_external_account',
            'card_external_account',
            'is_verified',
        )

    @swagger_serializer_method(serializer_or_field=BankAccountSerializer)
    def get_bank_external_account(self, obj):
        """Shortcut to filter only `bank` external account."""
        return self._filter_accounts_by_type('bank_account', obj)

    @swagger_serializer_method(serializer_or_field=CardSerializer)
    def get_card_external_account(self, obj):
        """Shortcut to filter only `card` external account."""
        return self._filter_accounts_by_type('card', obj)

    def _filter_accounts_by_type(
        self, obj_type: str, obj
    ) -> Union[dict, None]:
        """Shortcut to get first available account by `obj_type`.

        Filter only `first` account cause Express accounts dashboard allows to
        add only one account.

        """
        if not hasattr(obj, 'info'):
            return
        accounts = obj.info.external_accounts.get('data', [])
        accounts = list(filter(lambda x: x['object'] == obj_type, accounts))
        return accounts[0] if accounts else None
