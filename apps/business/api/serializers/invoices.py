import datetime
import logging
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q

from rest_framework import serializers

import stripe

from ....core.api.serializers import BaseSerializer
from ....finance.models import CustomerProxy
from ....users.api.serializers import (
    AppUserWithoutTypeSerializer,
    ClientInfoSerializer,
)
from ... import models, services
from .extra import AttachmentSerializer, PaymentMethodsSerializer
from .links import InvoiceActivitySerializer, InvoiceLogSerializer
from .matter import ShortMatterSerializer

logger = logging.getLogger('stripe')


class TimeEntrySerializer(BaseSerializer):
    """Serializer for time entry model."""
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all()
    )
    billing_item = serializers.PrimaryKeyRelatedField(
        queryset=models.BillingItem.objects.all(), required=False
    )

    class Meta:
        model = models.TimeEntry
        fields = (
            'start_time',
            'end_time',
            'billing_item',
            'created_by'
        )
        read_only_fields = (
            'end_time',
        )
        write_only_fields = (
            'start_time',
            'billing_item',
            'created_by',
        )


class BillingItemSerializer(BaseSerializer):
    """Serializer for BillingItem Model"""
    matter_data = ShortMatterSerializer(source='matter', read_only=True)
    created_by_data = AppUserWithoutTypeSerializer(
        source='created_by',
        read_only=True
    )
    # add field for backward compatibility with old apps v0.0
    invoice = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=models.Invoice.objects.none(),
        allow_null=True,
        required=False
    )
    billed_by_data = AppUserWithoutTypeSerializer(
        source='billed_by',
        read_only=True
    )
    client_data = ClientInfoSerializer(
        source='client',
        read_only=True
    )
    attachments_data = AttachmentSerializer(
        source='attachments',
        read_only=True,
        many=True
    )
    time_entries = serializers.SerializerMethodField(read_only=True)

    def get_time_entries(self, obj):
        return TimeEntrySerializer(obj.time_entries.all(), many=True).data

    class Meta:
        model = models.BillingItem
        fields = (
            'id',
            'matter',
            'client',
            'client_data',
            'is_billable',
            'billed_by',
            'billed_by_data',
            'matter_data',
            'created_by',
            'created_by_data',
            'invoice',
            'description',
            'time_spent',
            'hourly_rate',
            'currency',
            'date',
            'available_for_editing',
            'created',
            'modified',
            'quantity',
            'billing_type',
            'rate',
            'total_amount',
            'attachments',
            'attachments_data',
            'time_entries',
            'is_billed',
        )
        read_only_fields = (
            'created_by',
            'matter_data',
            'is_billed',
            'attachments',
            'available_for_editing',
            'billed_by_data'
        )

    def __init__(self, *args, **kwargs):
        """Restrict invoices and matters qs to only available for user ones."""
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['invoice'].queryset = models.Invoice.objects.\
                available_for_user(self.user).available_for_editing()
            self.fields['matter'].queryset = models.Matter.objects \
                .available_for_user(self.user)

    def validate(self, attrs):
        """Overridden validation to perform `invoice` as `invoice attachment`.

        If `invoice` is set in request data we need to validate if invoice and
        time billing can be correctly connected via `invoice attachment` and
        created attachment will be valid.

        """

        if attrs.get(
             'billing_type') == models.BillingItem.BILLING_TYPE_EXPENSE:
            attachments = self.context['request'].data.get('attachments', [])
            if len(attachments) == 0:
                raise serializers.ValidationError(
                    'Attachements are required for expenses'
                )

        if attrs.get(
             'billing_type') != models.BillingItem.BILLING_TYPE_TIME:
            if not attrs.get('total_amount'):
                raise serializers.ValidationError(
                    'Total amount are required for expenses'
                )

        if attrs.get(
             'billing_type') == models.BillingItem.BILLING_TYPE_TIME:
            if not attrs.get('time_spent') or not attrs.get('hourly_rate'):
                raise serializers.ValidationError(
                    "Hourly rate and Time is required for time"
                )

        invoice = attrs.pop('invoice', None)
        attrs = super().validate(attrs)
        if not invoice:
            return attrs

        attachment = models.BillingItemAttachment(
            invoice=invoice,
            time_billing=self.instance or self.prepare_instance(attrs),
        )
        attachment.clean()
        return attrs

    def to_representation(self, instance):
        """Improve time billings representation for not `hourly` rated matters

        Represent `fees` as `null` field instead of 0 for not `hourly` rated
        matters.

        """
        data = super().to_representation(instance)
        # Total amount will be represented by fee field
        data.pop('total_amount', None)
        amount = instance.fee
        data['fees'] = amount
        return data

    def create(self, validated_data):
        """Remember current request user as `creator`."""
        validated_data['created_by'] = self.user
        billing_item = super().create(validated_data)
        attachments = self.context['request'].data.get('attachments', [])
        attachments = [{'file': attachment} for attachment in attachments]
        serializer = AttachmentSerializer(data=attachments, many=True)
        serializer.is_valid(raise_exception=True)
        saved_files = serializer.save()
        for file in saved_files:
            billing_item.attachments.add(file)
        return billing_item

    def update(self, instance, validated_data):
        attachments = self.context['request'].data.get('attachments', [])
        for obj in instance.attachments.all():
            models.Attachment.objects.filter(id=obj.id).delete()
            instance.attachments.remove(obj)
        attachments = [{'file': attachment} for attachment in attachments]
        serializer = AttachmentSerializer(data=attachments, many=True)
        serializer.is_valid(raise_exception=True)
        saved_files = serializer.save()
        for file in saved_files:
            instance.attachments.add(file)
        return super().update(instance, validated_data)


class BillingItemShortSerializer(BillingItemSerializer):
    """BillingItemShortSerializer for display"""

    class Meta(BillingItemSerializer.Meta):

        fields = (
            'id',
            'matter',
            'client',
            'billed_by',
            'billed_by_data',
            'description',
            'time_spent',
            'hourly_rate',
            'currency',
            'date',
            'created',
            'modified',
            'quantity',
            'billing_type',
            'rate',
            'is_billable'
        )


class UpdateBillingItemSerializer(BillingItemSerializer):
    """BillingItemSerializer for updates."""
    # add field for backward compatibility with old apps v0.0
    invoice = serializers.ReadOnlyField()

    class Meta(BillingItemSerializer.Meta):
        read_only_fields = BillingItemSerializer.Meta.read_only_fields + (
            'matter',
        )


class InvoiceSerializer(BaseSerializer):
    """Serializer for Invoice Model"""
    matter_data = ShortMatterSerializer(source='matter', read_only=True)
    client_data = ClientInfoSerializer(
        source='client',
        read_only=True
    )
    attorney = serializers.PrimaryKeyRelatedField(
        source='matter.attorney',
        read_only=True,
    )
    attorney_data = AppUserWithoutTypeSerializer(
        source='matter.attorney.user',
        read_only=True
    )
    created_by_data = AppUserWithoutTypeSerializer(
        source='created_by',
        read_only=True
    )
    billing_items = serializers.PrimaryKeyRelatedField(
        queryset=models.BillingItem.objects.all(),
        many=True
    )
    billing_items_data = BillingItemShortSerializer(
        source='billing_items',
        many=True,
        read_only=True
    )
    activities_data = InvoiceActivitySerializer(
        source='activities',
        many=True,
        read_only=True
    )
    logs_data = InvoiceLogSerializer(
        source='logs',
        many=True,
        read_only=True
    )
    payment_method_data = PaymentMethodsSerializer(
        source='payment_method',
        many=True,
        read_only=True
    )
    title = serializers.SerializerMethodField(read_only=True)
    billable_sum = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Invoice
        fields = (
            'id',
            'number',
            'invoice_id',
            'email',
            'matter',
            'matter_data',
            'client',
            'client_data',
            'attorney',
            'attorney_data',
            'billing_items',
            'billing_items_data',
            'billable_sum',
            'created_by',
            'created_by_data',
            'period_start',
            'period_end',
            'due_date',
            'status',
            'payment_status',
            'note',
            'title',
            'total_amount',
            'time_billed',
            'fees_earned',
            'created',
            'modified',
            'finalized',
            'due_days',
            'note',
            'tax_rate',
            'payment_method',
            'payment_method_data',
            'activities_data',
            'logs_data',
        )
        relations = (
            'billing_items',
            'payment_method'
        )
        read_only_fields = (
            'created_by',
            'payment_status',
            'fees_earned',
            'fees_earned',
            'total_amount',
        )
        extra_kwargs = {
            'period_start': {
                'required': False
            },
            'period_end': {
                'required': False
            },
            'number': {
                'required': False
            },
            'client': {
                'required': False
            },
            'status': {
                'required': False
            }
        }

    def get_title(self, obj):
        """Return title of invoice"""
        return f"Invoice from {obj.client}"

    def get_billable_sum(self, obj):
        """Return sum of billable items"""
        sum = 0
        for item in obj.billing_items.all():
            if item.is_billable:
                sum += item.fee
        return sum

    def __init__(self, *args, **kwargs):
        """Not allow to create invoices for not available matters."""
        super().__init__(*args, **kwargs)
        if not self.user:
            return
        self.fields['matter'].queryset = models.Matter.objects\
            .available_for_user(self.user)

    def validate(self, attrs):
        if attrs.get('client', None) and attrs.get('matter', None):
            attrs['client'] = attrs['matter'].client
        if len(attrs.get('billing_items', [])) == 0:
            raise ValidationError(
                'There are no billing items in this invoice'
            )
        if attrs.get('billing_items', None):
            amount = sum([obj.fee for obj in attrs['billing_items']])
            if amount > 999999.99:
                raise ValidationError('Exceed maximum amount')
        view = self.context.get('view')
        if models.Invoice.objects.exclude(
            status=models.Invoice.INVOICE_STATUS_DRAFT
        ).filter(
            billing_items__in=attrs['billing_items']
        ).count() > 0 and view.action == 'create':
            raise ValidationError(
                (
                    'One or more of these billing '
                    'items has been previously invoiced'
                )
            )
        elif models.Invoice.objects.exclude(
            Q(id=self.get_instance().pk) |
            Q(status=models.Invoice.INVOICE_STATUS_DRAFT)
        ).filter(
            billing_items__in=attrs['billing_items']
        ).count() > 0:
            raise ValidationError(
                (
                    'One or more of these billing '
                    'items has been previously invoiced'
                )
            )
        if attrs.get('client', None):
            try:
                CustomerProxy.objects.get(
                    subscriber=attrs['client'].user
                )
            except CustomerProxy.DoesNotExist:
                raise ValidationError(
                    'Client profile does not exist in stripe'
                )
        return super().validate(attrs)

    def create(self, validated_data):
        """Remember current request user as `creator`."""
        validated_data['created_by'] = self.user
        validated_data['period_start'] = date.today()
        validated_data['period_end'] = date.today() + \
            datetime.timedelta(days=validated_data['due_days'])
        validated_data['due_date'] = validated_data['period_end']
        validated_data['activities'] = []
        validated_data['logs'] = []
        invoice = super().create(validated_data)
        try:
            customer = CustomerProxy.objects.get(
                subscriber=validated_data['client'].user
            )
            amount = sum([obj.fee for obj in invoice.billing_items.all()])
            invoice_item = stripe.InvoiceItem.create(
                customer=customer.id,
                amount=int(amount) * 100,
                currency='usd',
            )
            services.create_invoice_item(invoice, invoice_item)
            draft_invoice = stripe.Invoice.create(
                customer=customer.id,
                collection_method='send_invoice',
                days_until_due=validated_data['due_days'],
            )
            services.create_draft_invoice(invoice, draft_invoice)
            invoice.number = draft_invoice.number
            invoice.invoice_id = draft_invoice.id
            invoice.save()
        except stripe.error.StripeError as e:
            logger.error(e)
        except CustomerProxy.DoesNotExist as e:
            logger.error(e)
        except stripe.error.InvalidRequestError as e:
            logger.error(e)
        return invoice

    def update(self, invoice, validated_data):
        status = validated_data.pop('status', None)
        if status == 'open' and invoice.status == 'draft':
            invoice.send()
        return super().update(invoice, validated_data)

    def to_representation(self, instance):
        """Update invoice status"""
        if instance.due_date and date.today() > instance.due_date and \
                instance.status == models.Invoice.INVOICE_STATUS_OPEN:
            instance.status = models.Invoice.INVOICE_STATUS_OVERDUE
            instance.save()
        return super().to_representation(instance)


class InvoiceClientOverviewSerializer(BaseSerializer):
    """Serializes upcoming payments/invoices for client dashboard."""
    id = serializers.CharField(
        source='pk',
        read_only=True
    )
    invoice_id = serializers.CharField(
        source='number',
        read_only=True
    )
    due_date = serializers.DateField(
        read_only=True
    )
    invoice_from = serializers.CharField(
        source='created_by.attorney.firm_name',
        read_only=True
    )
    amount = serializers.CharField(
        source='fees_earned',
        read_only=True
    )

    class Meta:
        model = models.Invoice
        fields = (
            'id',
            'invoice_id',
            'title',
            'invoice_from',
            'status',
            'due_date',
            'amount'
        )


class InvoiceShortSerializer(InvoiceClientOverviewSerializer):

    class Meta(InvoiceSerializer.Meta):
        fields = (
            'id',
            'status',
            'due_date',
            'amount'
        )


class SendInvoiceSerializer(serializers.Serializer):
    """Serializer for sending invoices to clients."""
    recipient_list = serializers.ListField(
        allow_empty=False,
        child=serializers.EmailField()
    )
    note = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
