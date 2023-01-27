import logging
from datetime import datetime

from django.db.models import Q
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

import stripe
from django_fsm import TransitionNotAllowed

from libs.django_fcm.exceptions import TransitionFailedException

from ....core.api import views
from ... import models
from ...services import clone_invoice
from .. import filters, pagination, permissions, serializers
from ..serializers.invoices import TimeEntrySerializer
from .core import BusinessViewSetMixin

logger = logging.getLogger('django')


class BillingItemViewSet(BusinessViewSetMixin, views.CRUDViewSet):
    """CRUD api viewset for BillingItem model."""
    queryset = models.BillingItem.objects.select_related(
        'client',
        'client__user',
        'matter',
        'created_by',
        'billed_by',
        'currency',
    ).prefetch_related(
        'invoices',
        'attachments',
        'time_entries',
        'billing_items_invoices',
    )
    pagination_class = pagination.BillingItemLimitOffsetPagination
    serializer_class = serializers.BillingItemSerializer
    serializers_map = {
        'update': serializers.UpdateBillingItemSerializer,
        'partial_update': serializers.UpdateBillingItemSerializer,
    }
    can_edit_permissions = (
        BusinessViewSetMixin.attorney_support_permissions,
        permissions.CanEditOrDeleteInvoiceOrBillingItem,
    )
    permissions_map = {
        'create': (BusinessViewSetMixin.support_permissions,),
        'update': can_edit_permissions,
        'partial_update': can_edit_permissions,
        'destroy': can_edit_permissions,
    }
    filterset_class = filters.BillingItemFilter
    search_fields = (
        'description',
        'matter__title',
        'matter__code',
        'invoices__title'
    )
    ordering_fields = (
        'id',
        'date',
        'created',
        'modified',
        'description',
        'matter__title',
        'client___user__first_name',
        'billed_by__first_name'
    )

    def get_queryset(self):
        qs = super().get_queryset().filter(
            Q(billed_by=self.request.user) |
            Q(created_by=self.request.user) |
            Q(matter__shared_with__in=[self.request.user])
        ).distinct()
        empty_billing_ids = [
            obj.pk for obj in qs if obj.billing_items_invoices.count() == 0
        ]
        qs = qs.filter(pk__in=empty_billing_ids)
        return qs

    @action(methods=['POST'], detail=False)
    def start_timer(self, request, *args, **kwargs):
        """Starts timer for the logged in user."""

        # Validate if timer is already running for current user
        # Create new time entry if its not running already
        # else return elapsed time
        start_time_str = request.data.get('start_time', None)
        start_time = timezone.now()
        if start_time_str:
            t = datetime.strptime(start_time_str, "%H:%M:%S")
            start_time = timezone.now() - timezone.timedelta(
                hours=t.hour, minutes=t.minute, seconds=t.second
            )
        time_entry = models.TimeEntry.get_running_time_entry(request.user)
        if time_entry is None:
            time_entry = TimeEntrySerializer(
                data={
                    'created_by': request.user.id,
                    'start_time': start_time
                }
            )
            time_entry.is_valid(raise_exception=True)
            time_entry.save()
        elif time_entry and start_time_str:
            time_entry.start_time = start_time
            time_entry.save()

        elapsed_time, _ = models.TimeEntry.elapsed_time_without_microseconds(
            request.user
        )

        return Response(
            {
                'elapsed_time': elapsed_time
            },
            status=status.HTTP_201_CREATED
        )

    @action(methods=['POST'], detail=False)
    def stop_timer(self, request, *args, **kwargs):
        """Stops timer for the logged in user."""
        time_entry = models.TimeEntry.get_running_time_entry(request.user)
        if time_entry is None:
            return Response(
                {"error": "Timer needs to be started before stopping."},
                status=status.HTTP_400_BAD_REQUEST
            )
        time_entry.end_time = timezone.now()
        time_entry.save()
        elapsed_time, _ = models.TimeEntry.elapsed_time_without_microseconds(
            request.user
        )

        return Response(
            {
                'elapsed_time': elapsed_time
            },
            status=status.HTTP_202_ACCEPTED
        )

    @action(methods=['POST'], detail=False)
    def cancel_timer(self, request, *args, **kwargs):
        """Cancel timer for the logged in user."""
        user = request.user
        models.TimeEntry.objects.filter(created_by=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'], detail=False)
    def get_current_elapsed_time(self, request, *args, **kwargs):
        """Returns elapsed time at the moment."""
        elapsed_time, is_running = (
                models.TimeEntry.elapsed_time_without_microseconds(
                   request.user
                )
        )

        return Response(
            {
                'elapsed_time': elapsed_time,
                'status': 'running' if is_running else 'stopped'
            },
            status=status.HTTP_200_OK
        )


class InvoiceViewSet(BusinessViewSetMixin, views.CRUDViewSet):
    """API viewset for Invoice model."""
    queryset = models.Invoice.objects.all().select_related(
        'created_by',
        'matter',
        'client__user',
        'matter__attorney',
        'matter__attorney__user',
        'matter__attorney__user__finance_profile',
        'matter__attorney__user__finance_profile__deposit_account',
        'matter__attorney__user__finance_profile__deposit_account__info',
    ).prefetch_related(
        'payment_method',
        'time_billing',
        'billing_items',
        'billing_items__billed_by',
        'activities',
        'logs',
    ).with_fees_earned().with_time_billed()

    can_edit_permissions = (
        BusinessViewSetMixin.attorney_support_permissions,
        permissions.CanEditOrDeleteInvoiceOrBillingItem,
    )

    permissions_map = {
        'create': (BusinessViewSetMixin.support_permissions,),
        'update': can_edit_permissions,
        'partial_update': can_edit_permissions,
        'destroy': can_edit_permissions,
    }

    serializer_class = serializers.InvoiceSerializer
    transition_result_serializer_class = serializers.InvoiceSerializer
    serializers_map = {
        'export': None,
        'draft': serializers.InvoiceSerializer,
        'send': None,
    }
    filterset_class = filters.InvoiceFilter
    search_fields = (
        'title',
        'matter__title',
        'matter__code',
        'matter__client__user__first_name',
        'matter__client__user__first_name',
        'matter__client__organization_name',
    )
    ordering_fields = (
        'id',
        'title',
        'number',
        'created',
        'modified',
        'due_date',
        'matter__title',
        'matter__client__organization_name',
    )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        fields = request.query_params.getlist('ordering', [])
        for field in fields:
            if 'total_amount' in field:
                reverse = False
                if field.startswith('-'):
                    reverse = True
                    field = field[1:]
                data = sorted(
                    data,
                    key=lambda k: (k[field] is not None, k[field]),
                    reverse=reverse
                )
        if page is not None:
            return self.get_paginated_response(data)
        else:
            return Response(data)

    def create(self, request, *args, **kwargs):
        try:
            serializer = serializers.InvoiceSerializer(
                data=request.data, context=super().get_serializer_context()
            )
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            headers = self.get_success_headers(data)
            invoice = serializer.save()
            invoice.send()
            invoice.save()
            serializer = serializers.InvoiceSerializer(
                instance=invoice
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except TransitionFailedException:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'detail': 'The invoice can not be sent'}
            )

    @action(methods=['GET'], detail=True)
    def export(self, request, *args, **kwargs):
        """Export invoice as PDF file.

        Return:
            response(HttpResponse) - response with attachment

        """
        obj = self.get_object()
        try:
            return Response(
                data={
                    "link": stripe.Invoice.retrieve(obj.invoice_id).invoice_pdf
                },
                status=status.HTTP_200_OK
            )
        except stripe.error.StripeError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=['POST'], detail=True)
    def open(self, *args, **kwargs):
        """Send invoice email to client."""
        try:
            invoice = self.get_object()
            if models.Invoice.objects.exclude(
                Q(id=invoice.pk) |
                Q(status=models.Invoice.INVOICE_STATUS_DRAFT)
            ).filter(
                billing_items__in=[49]
            ).count() > 0:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": (
                        'One or more of these billing '
                        'items has been previously invoiced'
                    )}
                )
            invoice.send()
            invoice.save()
            return Response(
                status=status.HTTP_200_OK,
            )
        except TransitionFailedException as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": str(e)}
            )
        except TransitionNotAllowed as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": str(e)}
            )

    @action(methods=['POST'], detail=True)
    def duplicate(self, request, *args, **kwargs):
        invoice = self.get_object()
        duplicated_invoice = clone_invoice(invoice)
        duplicated_invoice.status = models.Invoice.INVOICE_STATUS_DRAFT
        duplicated_invoice.save()
        serializer = serializers.InvoiceSerializer(
            instance=duplicated_invoice
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['POST'], detail=False)
    def draft(self, request, *args, **kwargs):
        """Draft invoice."""
        serializer = serializers.InvoiceSerializer(
            data=request.data, context=super().get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        headers = self.get_success_headers(data)
        invoice = serializer.save()
        serializer = serializers.InvoiceSerializer(
            instance=invoice
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(methods=['POST'], detail=True)
    def pay(self, request, *args, **kwargs):
        """Pay invoice."""
        invoice = self.get_object()
        try:
            invoice.pay()
            invoice.save()
            return Response(
                data=serializers.InvoiceSerializer(invoice).data,
                status=status.HTTP_200_OK,
            )
        except TransitionNotAllowed as e:
            return Response(
                data={'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except TransitionFailedException as e:
            return Response(
                data={'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
