from django_filters import rest_framework as filters
from django_filters.rest_framework import NumberFilter
from django_filters.widgets import RangeWidget

from .. import models


class LeadFilter(filters.FilterSet):
    """Filter by nested fields for Lead model."""

    class Meta:
        model = models.Lead
        fields = {
            'id': ['exact', 'in'],
            'priority': ['exact', 'in'],
            'attorney': ['exact', 'in'],
            'client': ['exact', 'in'],
            'status': ['exact', 'in'],
        }


class OpportunityFilter(filters.FilterSet):
    """Filter by nested fields for Opportunity model."""

    class Meta:
        model = models.Opportunity
        fields = {
            'id': ['exact', 'in'],
            'priority': ['exact', 'in'],
            'attorney': ['exact', 'in'],
            'client': ['exact', 'in'],
        }


class MatterFilter(filters.FilterSet):
    """Filter by nested fields for Matter model."""
    shared_with = NumberFilter(
        method='filter_shared_with'
    )

    class Meta:
        model = models.Matter
        fields = {
            'id': ['exact', 'in'],
            'lead': ['exact', 'in'],
            'attorney': ['exact', 'in'],
            'client': ['exact', 'in'],
            'country': ['exact', 'in'],
            'city': ['exact', 'in'],
            'state': ['exact', 'in'],
            'status': ['exact', 'in'],
            'stage': ['exact', 'in'],
            'speciality': ['exact', 'in'],
        }

    def filter_shared_with(self, queryset, name, value):
        """Filter matter which is shared with me"""
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.filter(shared_with__in=[value])


class BillingItemFilter(filters.FilterSet):
    """Filter by nested fields for BillingItem model."""
    invoice = filters.NumberFilter(method='filter_by_invoice')

    class Meta:
        model = models.BillingItem
        fields = {
            'id': ['exact', 'in'],
            'matter': ['exact', 'in'],
            'billing_type': ['exact', 'in'],
            'is_billable': ['exact', 'in'],
            'date': ['gte', 'lte'],
            'created': ['gte', 'lte'],
        }

    def filter_by_invoice(self, queryset, name, value):
        """Filter time billings for invoice."""
        if value:
            return queryset.filter(attached_invoice__invoice=value)
        return queryset


class InvoiceFilter(filters.FilterSet):
    """Filter by nested fields for Invoice model."""

    class PeriodRangeWidget(RangeWidget):
        """To customize suffixes for `period` filter."""
        suffixes = ['start', 'end']

    period = filters.DateFromToRangeFilter(
        widget=PeriodRangeWidget,
        method='filter_period',
        help_text=(
            "This is not the filter field you're looking for, "
            'use `period_start` and `period_end`'
        )
    )
    # DateFromToRangeFilter looking for `period_start` and `period_end`
    # we add these two for swagger spec
    period_start = filters.CharFilter(
        method='filter_without_filtration',
        help_text='Example: `2020-01-10`'
    )
    period_end = filters.CharFilter(
        method='filter_without_filtration',
        help_text='Example: `2020-01-10`'
    )

    matter__client__first_name__istartswith = filters.CharFilter(
        lookup_expr='istartswith',
        field_name='matter__client__user__first_name'
    )
    matter__client__first_name__icontains = filters.CharFilter(
        lookup_expr='icontains',
        field_name='matter__client__user__first_name'
    )
    matter__client__last_name__istartswith = filters.CharFilter(
        lookup_expr='istartswith',
        field_name='matter__client__user__last_name'
    )
    matter__client__last_name__icontains = filters.CharFilter(
        lookup_expr='icontains',
        field_name='matter__client__user__last_name'
    )

    class Meta:
        model = models.Invoice
        fields = {
            'id': ['exact', 'in'],
            'created_by': ['exact', 'in'],
            'client': ['exact', 'in'],
            'matter': ['exact', 'in'],
            'matter__attorney': ['exact', 'in'],
            'matter__client': ['exact', 'in'],
            'title': ['istartswith', 'icontains'],
            'matter__client__organization_name': ['istartswith', 'icontains'],
            'status': ['exact', 'in'],
            'payment_status': ['exact', 'in'],
            'period_start': [
                'year__gte',
                'year__lte',
                'month__gte',
                'month__lte',
            ],
            'period_end': [
                'year__gte',
                'year__lte',
                'month__gte',
                'month__lte',
            ],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }

    def filter_period(self, queryset, name, value: slice):
        """Filter invoices which are in input time period."""
        if value and value.start and value.stop:
            period_start = value.start
            period_end = value.stop
            return queryset.match_period(
                period_start=period_start,
                period_end=period_end
            )
        return queryset

    def filter_without_filtration(self, queryset, *args, **kwargs):
        """Filter method, that returns original queryset.

        Dummy filter method to add extra query params to swagger specs that
        are not used in filters, but we need to show them in swagger spec.

        """
        return queryset


class ActivityFilter(filters.FilterSet):
    """Filter for `Activity` model."""

    class Meta:
        model = models.Activity
        fields = {
            'id': ['exact', 'in'],
            'user': ['exact', 'in'],
            'title': ['icontains', 'istartswith'],
            'matter': ['exact', 'in'],
            'matter__client': ['exact', 'in'],
            'type': ['exact', 'in'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }


class NoteFilter(filters.FilterSet):
    """Filter for `Note` model."""

    class Meta:
        model = models.Note
        fields = {
            'id': ['exact', 'in'],
            'title': ['icontains', 'istartswith'],
            'matter': ['exact', 'in'],
            'matter__attorney': ['exact', 'in'],
            'matter__client': ['exact', 'in'],
            'created_by': ['exact', 'in'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }


class MatterPostFilter(filters.FilterSet):
    """Filter for `MatterPost` model."""

    class Meta:
        model = models.MatterPost
        fields = {
            'id': ['exact', 'in'],
            'title': ['icontains', 'istartswith'],
            'matter': ['exact', 'in'],
            'matter__attorney': ['exact', 'in'],
            'matter__client': ['exact', 'in'],
            'seen': ['exact', 'in'],
            'seen_by_client': ['exact', 'in'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }


class MatterCommentFilter(filters.FilterSet):
    """Filter for `MatterComment` model."""

    class Meta:
        model = models.MatterComment
        fields = {
            'post': ['exact', 'in'],
            'text': ['icontains', 'istartswith'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }


class VoiceConsentFilter(filters.FilterSet):
    """Filter for `VoiceConsent` model."""

    class Meta:
        model = models.VoiceConsent
        fields = {
            'matter': ['exact', 'in'],
            'title': ['icontains', 'istartswith'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }


class VideoCallFilter(filters.FilterSet):
    """Filter for `VideoCall` model."""

    class Meta:
        model = models.VideoCall
        fields = {
            'id': ['exact', 'in'],
            'participants': ['exact'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }


class ChecklistEntryFilter(filters.FilterSet):
    """Filter for `ChecklistEntry` model (just for swagger spec)."""
    matter = filters.NumberFilter(method='noop_filter')

    class Meta:
        model = models.ChecklistEntry
        fields = {
            'id': ['exact', 'in'],
        }

    def noop_filter(self, queryset, name, value):
        """No filtration (implemented on view level)"""
        return queryset


class StageFilter(ChecklistEntryFilter):
    """Filter for `Stage` model (just for swagger spec)."""

    class Meta:
        model = models.Stage
        fields = {
            'id': ['exact', 'in'],
            'attorney': ['exact', 'in']
        }


class MatterSharedWithFilter(filters.FilterSet):
    """Filter for `MatterSharedWith` model."""

    class Meta:
        model = models.MatterSharedWith
        fields = {
            'id': ['exact', 'in'],
            'user': ['exact', 'in'],
            'matter': ['exact', 'in'],
        }


class PostedMatterFilter(filters.FilterSet):
    """Filter for `PostedMatter` model."""

    class Meta:
        model = models.PostedMatter
        fields = {
            'id': ['exact', 'in'],
            'client': ['exact', 'in'],
            'status': ['exact', 'in'],
            'is_hidden_for_client': ['exact', 'in'],
            'is_hidden_for_attorney': ['exact', 'in'],
        }


class ProposalFilter(filters.FilterSet):
    """Filter for `Proposal` model."""

    class Meta:
        model = models.Proposal
        fields = {
            'id': ['exact', 'in'],
            'attorney': ['exact', 'in'],
            'post': ['exact', 'in'],
            'status': ['exact', 'in'],
            'is_hidden_for_client': ['exact', 'in'],
            'is_hidden_for_attorney': ['exact', 'in'],
        }
