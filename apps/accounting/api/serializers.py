from rest_framework import serializers

from apps.business.models import Invoice


class AccessAllowedSerializer(serializers.Serializer):
    """Serializer to represent successful auth callback from Quickbooks.

    It is used by QB callback when user approves app access request.

    """
    code = serializers.CharField(required=True)
    realmId = serializers.CharField(required=True)
    state = serializers.CharField(required=True)


class AccessDeniedSerializer(serializers.Serializer):
    """Serializer to represent error auth callback from Quickbooks.

    It is used by QB callback when user denies app access request.

    """
    error = serializers.CharField(required=True)
    state = serializers.CharField(required=True)


class CustomerSerializer(serializers.Serializer):
    """Serializer to represent QuickBooks `Customer` data."""
    id = serializers.IntegerField(source='Id')
    display_name = serializers.CharField(source='DisplayName')
    first_name = serializers.CharField(source='GivenName')
    last_name = serializers.CharField(source='FamilyName')
    email = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='CompanyName')

    def get_email(self, obj) -> str:
        """Get email from `PrimaryEmailAddr` data."""
        email_data = obj['PrimaryEmailAddr']
        return email_data['Address'] if email_data else ''


class ExportInvoiceSerializer(serializers.Serializer):
    """Serializer to validate `Export Invoice` request."""
    invoice = serializers.PrimaryKeyRelatedField(
        queryset=Invoice.objects.none(),
        required=True
    )
    customer = serializers.IntegerField(required=False, allow_null=True)

    def __init__(self, qb_api_client=None, *args, **kwargs):
        """Restrict invoices to only available for user ones."""
        super().__init__(*args, **kwargs)
        self.qb_api_client = qb_api_client
        request = self.context.get('request')
        if not request or not request.user.is_attorney:
            return
        self.fields['invoice'].queryset = Invoice.objects.all() \
            .available_for_user(request.user)

    def validate_invoice(self, invoice):
        """Validate that invoice has time billings."""
        if invoice.time_billing.count() == 0:
            raise serializers.ValidationError(
                'Invoice should have time billings'
            )
        return invoice

    def validate_customer(self, customer):
        """Validate that defined customer exists in QuickBooks."""
        if customer:
            customer = self.qb_api_client.get_customer(customer)
        return customer
