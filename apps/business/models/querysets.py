from datetime import datetime, timedelta
from functools import reduce

from django.db.models import (
    BooleanField,
    Case,
    Count,
    DecimalField,
    F,
    Q,
    Sum,
    When,
)
from django.db.models.query import QuerySet

from ...finance.models.payments.querysets import AbstractPaidObjectQuerySet
from ...users import models as user_models

__all__ = (
    'UserRelatedQuerySet',
    'MatterRelatedQuerySet',
    'LeadQuerySet',
    'MatterQuerySet',
    'BillingItemQuerySet',
    'InvoiceQuerySet',
    'MatterCommentQuerySet',
    'MatterPostQuerySet',
    'NoteQuerySet',
    'VoiceConsentQuerySet',
    'VideoCallQuerySet',
    'MatterSharedWithQuerySet',
)


class UserRelatedQuerySet(QuerySet):
    """Queryset class which provides `available_for_user` filtration.

    This queryset provides filtration for availability of related to user
    objects.

    To use these qs methods model should have `attorney` and `client`
    attributes.

    """

    def available_for_user(self, user: user_models.AppUser):
        """Filter available for user objects.

        Cases:
            1. Request user is attorney - filter only instances where user is
            attorney.

            2. Request user is client - filter only instances where user is
            client.

        """
        # Fix for swagger spec
        # if user.user_type == user_models.AppUser.USER_TYPE_STAFF:
        #     return self
        lookup = 'attorney' if user.is_attorney else 'client'
        try:
            return self.filter(
                Q(**{lookup: user.pk}) |
                Q(**{'referral__attorney': user.pk}) |
                Q(**{'shared_with__in': [user]})
            )
        except Exception:
            try:
                return self.filter(
                    Q(**{lookup: user.pk}) | Q(**{'shared_with__in': [user]})
                )
            except Exception:
                return self.filter(**{lookup: user.pk})


class MatterRelatedQuerySet(QuerySet):
    """Queryset class which provides `available_for_user` filtration.

    This queryset provides filtration for availability of related to matter
    objects. So depending on matter availability related objects should be
    available or not too.

    """

    def available_for_user(self, user: user_models.AppUser):
        """Filter available for user matter-related instances.

        Cases:
            1. Request user is attorney - filter only instances related to
            matters where user is attorney or instances related to matter
            shared with user.

            2. Request user is client - filter only instances related to
            matters where user is client.

        """
        from . import Matter
        available_matters = Matter.objects.all().available_for_user(user)
        return self.filter(matter__in=available_matters)


class OpportunityQuerySet(UserRelatedQuerySet):
    """QuerySet class Opportunity model."""
    pass


class LeadQuerySet(UserRelatedQuerySet):
    """QuerySet class Lead model."""

    def aggregate_count_stats(self):
        """Get count statistics for Lead(by status)."""
        from . import Lead
        return self.aggregate(
            active_count=Count('pk', filter=Q(status=Lead.STATUS_ACTIVE)),
            converted_count=Count(
                'pk', filter=Q(status=Lead.STATUS_CONVERTED)
            ),
            total_count=Count('pk', ),
        )


class MatterQuerySet(UserRelatedQuerySet):
    """QuerySet class Matter model."""

    def available_for_user(self, user: user_models.AppUser):
        """Filter available for user objects.

        Cases:
            1. Request user is attorney - filter only instances where user is
            attorney or matters shared with user (except matters in `pending`
            or `draft` states cause they can't be shared).

            2. Request user is client - filter only instances where user is
            client.

        """
        from ..models import Matter
        qs = super().available_for_user(user)
        if user.is_staff:
            return qs

        shared_matters = user.shared_matters.exclude(
            status__in=[Matter.STATUS_OPEN]
        )
        return self.filter(
            Q(id__in=qs.values('id')) | Q(id__in=shared_matters)
        )

    def open(self):
        """Shortcut to get only `open` matters."""
        # import here because of cyclic dependency
        from . import Matter
        return self.filter(status=Matter.STATUS_OPEN)

    def hourly_rated(self):
        """Shortcut to get only `hourly` rated matters."""
        # import here because of cyclic dependency
        from . import Matter
        return self.filter(rate_type=Matter.RATE_TYPE_HOURLY)

    def with_invoices_num(self):
        """Annotate each Matter with invoices count."""
        return self.annotate(num_invoices=Count('invoices'))

    def with_totals(self):
        """Annotate each Matter with billed time total `fees` and `hours`.

        This annotation is needed to improve performance of getting totals:

            - `time_billed` (total spent time)
            - `fees_earned` (total fees)

        """
        return self.annotate(
            _time_billed=Sum('billing_item__time_spent'),
            _fees_earned=Sum(
                F('billing_item__rate') * F('billing_item__quantity'),
                output_field=DecimalField()
            ),
        )

    def aggregate_count_stats(self):
        """Get count statistics for Matter(by status)."""
        from . import Matter
        return self.aggregate(
            open_count=Count('pk', filter=Q(status=Matter.STATUS_OPEN)),
            referred_count=Count(
                'pk', filter=Q(status=Matter.STATUS_REFERRAL)
            ),
            closed_count=Count('pk', filter=Q(status=Matter.STATUS_CLOSE)),
            total_count=Count('pk', ),
        )

    def with_time_billings(
        self,
        user: user_models.AppUser,
        period_start: datetime,
        period_end: datetime,
    ):
        """Add to qs calculated billed time and fees for period of time.

        It will be grouped by each matter.

        """
        return self.available_for_user(user).filter(
            billing_item__date__gte=period_start,
            billing_item__date__lte=period_end
        ).annotate(
            attorney_time_spent=Sum(
                'billing_item__time_spent',
                filter=Q(billing_item__created_by_id=user.pk)
            ),
            time_spent=Sum('billing_item__time_spent'),
            fees=Sum(
                F('billing_item__rate') * F('billing_item__quantity'),
                output_field=DecimalField()
            ),
            attorney_fees=Sum(
                F('billing_item__rate') * F('billing_item__quantity'),
                filter=Q(billing_item__created_by_id=user.pk),
                output_field=DecimalField()
            ),
        )

    def with_is_shared_for_user(self, user):
        """Annotate each Matter `_is_shared` flag.

        This annotation is needed to improve performance of getting matters and
        adds a flag which designates whether a matter is shared for user or
        not.

        """
        shared_matters = user.shared_matters.values('id')
        return self.annotate(
            _is_shared=Case(
                When(id__in=shared_matters, then=True),
                default=False,
                output_field=BooleanField()
            )
        )


class BillingItemQuerySet(MatterRelatedQuerySet):
    """QuerySet class BillingItem model."""

    def match_period(self, period_start: datetime, period_end: datetime):
        """Filter BillingItem to match period.

        BillingItem is considered as matching to period if its `date` is in a
        period from arguments.

        """
        return self.filter(date__gte=period_start, date__lte=period_end)

    def calculate_time_billing_for_period(
        self,
        user: user_models.AppUser,
        start_date: datetime,
        end_date: datetime,
    ) -> timedelta:
        """Calculate time billed for period of time."""
        return self.available_for_user(
            user
        ).filter(
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(
            Sum('time_spent')
        ).get('time_spent__sum')

    def get_total_fee(self):
        """Calculate total fees of billed time in qs.

        In case if qs related to only one matter and this matter has not
        `hourly` rate type -> return None, cause we can't calculate total fees
        amount for such matters.

        """
        # Comment out this part for null total_fee
        # check if original qs belongs to only 1 matter and check its rate type
        # if self.values('matter').distinct().count() == 1:
        #     # if matter is not hourly rated - return None total `fees` amount
        #     if not self.first().matter.is_hourly_rated:
        #         return
        return sum([obj.fee for obj in self.filter(is_billable=True)])

    def get_total_time(self):
        """Calculate total time of billed time in qs."""
        time_spent = self.aggregate(Sum('time_spent')) \
            .get('time_spent__sum')

        if not time_spent:
            return '00:00:00'

        return str(time_spent)

    def available_for_editing(self):
        """Filter tb that can be edited.

        Only time billings attached to invoices with payment status
        'not_started' can be edited.

        """
        from . import Invoice
        return self.filter(
            Q(invoices__payment_status__in=Invoice.AVAILABLE_FOR_EDITING_STATUSES) |  # noqa
            Q(invoices__isnull=True)
        )

    def with_available_for_editing(self):
        """Add annotation that shows tb can be edited or not."""
        from . import Invoice
        return self.annotate(
            _available_for_editing=Case(
                When(
                    Q(invoices__payment_status__in=Invoice.AVAILABLE_FOR_EDITING_STATUSES) |  # noqa
                    Q(invoices__isnull=True),
                    then=True
                ),
                default=False,
                output_field=BooleanField()
            )
        ).distinct()

    def with_is_paid(self):
        """Add annotation that shows tb is paid or not """
        from . import Invoice
        return self.annotate(
            _is_paid=Case(
                When(invoices__status=Invoice.PAYMENT_STATUS_PAID, then=True),
                default=False,
                output_field=BooleanField()
            )
        ).distinct()


class InvoiceQuerySet(AbstractPaidObjectQuerySet, MatterRelatedQuerySet):
    """QuerySet class Invoice model."""

    def match_date(self, date: datetime):
        """Filter Invoices which periods match `date`."""
        return self.filter(period_start__lte=date, period_end__gte=date)

    def match_period(self, period_start: datetime, period_end: datetime):
        """Filter Invoices which are in input time period.

        We return invoices that have at least one day of it's period inside
        input period. In other words we return invoices that: have period_end
        greater then input period_start and period_start less then input
        period_end. (If you have hard time understanding it, try to draw it).

        """
        return self.exclude(
            Q(period_end__lt=period_start) | Q(period_start__gt=period_end)
        )

    def available_for_user(self, user: user_models.AppUser):
        """Filter invoices available to user.

        Client can see all invoices except `pending`.

        """
        from . import Invoice
        available_invoices = super().available_for_user(user)
        if user.is_attorney or user.is_support or user.is_client:
            return available_invoices
        return available_invoices.exclude(
            status=Invoice.INVOICE_STATUS_OPEN
        )

    def available_for_editing(self):
        """Filter invoices can be edited.

        Only invoices with payment status 'not_started' can be
        edited.

        """
        from . import Invoice
        return self.filter(
            payment_status__in=Invoice.AVAILABLE_FOR_EDITING_STATUSES
        )

    def with_fees_earned(self):
        """Calculate earned fees for invoices."""
        return self.annotate(
            _fees_earned=Sum(
                F('time_billing__rate') * F('time_billing__quantity'),
                output_field=DecimalField()
            )
        )

    def with_time_billed(self):
        """Calculate amount of billed time."""
        return self.annotate(
            _time_billed=Sum('time_billing__time_spent')
        )


class MatterPostQuerySet(MatterRelatedQuerySet):
    """QuerySet class for `MatterPost` model."""


class MatterCommentQuerySet(MatterRelatedQuerySet):
    """QuerySet class for `MatterComment` model."""

    def available_for_user(self, user: user_models.AppUser):
        """Filter comments according to available matters to user."""
        from . import Matter
        available_matters = Matter.objects.all().available_for_user(user)
        return self.filter(post__matter__in=available_matters)


class NoteQuerySet(MatterRelatedQuerySet):
    """QuerySet class for `Note` model."""

    def available_for_user(self, user: user_models.AppUser):
        """Overridden method to return only created by user notes."""
        qs = super().available_for_user(user)
        return qs.filter(
            Q(created_by=user) |
            Q(matter__attorney__user=user) |
            Q(matter__client__user=user)
        )


class VoiceConsentQuerySet(MatterRelatedQuerySet):
    """QuerySet class for `VoiceConsent` model."""


class VideoCallQuerySet(QuerySet):
    """QuerySet class for `VideoCall` model."""

    def available_for_user(self, user: user_models.AppUser):
        """Get video calls: created by user or where user was invited."""
        return self.filter(participants=user)

    def get_by_participants(self, participants):
        """Get call by list of participants."""
        video_call_qs = self.annotate(
            participants_count=Count('participants')
        ).filter(
            participants_count=len(participants)
        )
        video_calls = reduce(
            lambda qs, pk: qs.filter(participants=pk),
            participants,
            video_call_qs
        )
        return video_calls.first()


class MatterSharedWithQuerySet(MatterRelatedQuerySet):
    """QuerySet class for `MatterSharedWith` model."""
