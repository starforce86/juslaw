import logging
import typing
from datetime import datetime

from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db import models
from django.db.models import Count, Q, Sum

from ...finance.models.payments.querysets import AbstractPaidObjectQuerySet
from .utils.verification import VerifiedRegistrationQuerySet

__all__ = (
    'InviteQuerySet',
    'AttorneyQuerySet',
    'ClientQuerySet',
    'AppUserQuerySet',
    'SupportQuerySet',
)


logger = logging.getLogger('django')


class InviteQuerySet(models.QuerySet):
    """Queryset class for `Invite` model."""

    def without_user(self):
        """Return invites without user."""
        return self.filter(user__isnull=True)

    def without_matter(self):
        """Return invites without matter."""
        return self.filter(matter__isnull=True)

    def only_invited_type(self):
        """Filter invites with `invited_by_user` type only."""
        from . import Invite
        return self.filter(type=Invite.TYPE_INVITED)


class AppUserQuerySet(models.QuerySet):
    """Queryset class for `AppUser` model."""

    def available_for_share(self, matter=None):
        """Get queryset of available for sharing users.

        These are:
            - verified attorneys with active subscription
            - verified paralegals users

        If `matter` is defined - remove already shared attorneys from qs.

        """
        from . import Attorney, Paralegal
        attorneys = Attorney.objects.verified() \
            .has_active_subscription().values_list('pk', flat=True)

        paralegals = Paralegal.objects.all().verified().values_list(
            'pk', flat=True
        )

        available = self.exclude(is_staff=True).filter(
            models.Q(id__in=attorneys) | models.Q(id__in=paralegals)
        )

        if not matter:
            return available

        available = set(available.values_list('id', flat=True))
        already_shared = set(matter.shared_with.values_list('id', flat=True))
        return self.filter(id__in=available - already_shared)

    def active(self):
        """Get queryset of only `active` appusers."""
        return self.filter(is_active=True)

    def attorneys(self):
        """Get queryset of appusers which are verified attorneys only."""
        from . import Attorney
        attorneys = Attorney.objects.real_users().verified() \
            .has_active_subscription()
        return self.filter(id__in=attorneys.values_list('user__id', flat=True))

    def clients(self):
        """Get queryset of client appusers."""
        return self.filter(client__isnull=False)

    def support(self):
        """Get queryset of verified support appusers."""
        from . import Support

        support = Support.objects.verified().paid()
        return self.filter(id__in=support.values_list('user__id', flat=True))

    def exclude_staff(self):
        """Remove staff users from queryset."""
        return self.exclude(is_staff=True)

    def is_registered(self, email):
        """Check email if it is already existed"""
        return self.filter(email__iexact=email).exists()


class AttorneyQuerySet(VerifiedRegistrationQuerySet):
    """Queryset class for `Attorney` model."""

    def with_distance(
        self,
        longitude: typing.Union[int, float, str],
        latitude: typing.Union[int, float, str],
    ):
        """Add distance annotation to attorney queryset.

        If invalid coordinates are sent, method will annotate queryset with
        distance = null. We can't simply return queryset(self), because we
        later in api use `distance` to order attorneys.

        """
        try:
            point = Point(
                x=float(longitude),
                y=float(latitude),
                srid=settings.LOCATION_SRID,
            )
        except (TypeError, ValueError) as error:
            logger.info(
                f'AttorneyQuerySet: Incorrect cords were passed: `{error}`'
            )
            return self.annotate(
                distance=models.Value(None, output_field=models.FloatField())
            )
        return self.annotate(
            distance=Distance('firm_location', point)
        )

    def has_lead_with_user(self, user):
        """Filter attorneys that client has lead with.

        If user is client, we filter queryset to return attorneys that client
        has a lead with.

        """
        if user.is_client:
            return self.filter(leads__client_id=user.pk)
        return self

    def real_users(self):
        """Return attorneys that are not staff users."""
        return self.filter(user__is_staff=False)

    def has_active_subscription(self):
        """Return attorneys with active subscription."""
        return self.exclude(user__active_subscription__isnull=True)

    def aggregate_count_stats(self):
        """Get count statistics for Attorney(by verification status)."""
        from . import Attorney
        return self.aggregate(
            verified_count=Count(
                'pk', filter=Q(
                    verification_status=Attorney.VERIFICATION_APPROVED
                )
            ),
            not_verified_count=Count(
                'pk', filter=Q(
                    verification_status=Attorney.VERIFICATION_NOT_VERIFIED
                )
            ),
            total_count=Count('pk', ),
        )


class ParalegalQuerySet(VerifiedRegistrationQuerySet):
    """Queryset class for `Paralegal` model."""

    def with_distance(
        self,
        longitude: typing.Union[int, float, str],
        latitude: typing.Union[int, float, str],
    ):
        """Add distance annotation to paralegal queryset.

        If invalid coordinates are sent, method will annotate queryset with
        distance = null. We can't simply return queryset(self), because we
        later in api use `distance` to order paralegals.

        """
        try:
            point = Point(
                x=float(longitude),
                y=float(latitude),
                srid=settings.LOCATION_SRID,
            )
        except (TypeError, ValueError) as error:
            logger.info(
                f'ParalegalQuerySet: Incorrect cords were passed: `{error}`'
            )
            return self.annotate(
                distance=models.Value(None, output_field=models.FloatField())
            )
        return self.annotate(
            distance=Distance('firm_location', point)
        )

    def has_lead_with_user(self, user):
        """Filter paralegals that client has lead with.

        If user is client, we filter queryset to return paralegals that client
        has a lead with.

        """
        if user.is_client:
            return self.filter(leads__client_id=user.pk)
        return self

    def real_users(self):
        """Return paralegals that are not staff users."""
        return self.filter(user__is_staff=False)

    def has_active_subscription(self):
        """Return paralegals with active subscription."""
        return self.exclude(user__active_subscription__isnull=True)

    def aggregate_count_stats(self):
        """Get count statistics for Paralegal(by verification status)."""
        from . import Paralegal
        return self.aggregate(
            verified_count=Count(
                'pk', filter=Q(
                    verification_status=Paralegal.VERIFICATION_APPROVED
                )
            ),
            not_verified_count=Count(
                'pk', filter=Q(
                    verification_status=Paralegal.VERIFICATION_NOT_VERIFIED
                )
            ),
            total_count=Count('pk', ),
        )


class EnterpriseQuerySet(VerifiedRegistrationQuerySet):
    """Queryset class for `Enterprise` model."""

    def real_users(self):
        """Return enterprises that are not staff users."""
        return self.filter(user__is_staff=False)

    def aggregate_count_stats(self):
        """Get count statistics for Enterprise(by verification status)."""
        from . import Enterprise
        return self.aggregate(
            verified_count=Count(
                'pk', filter=Q(
                    verification_status=Enterprise.VERIFICATION_APPROVED
                )
            ),
            not_verified_count=Count(
                'pk', filter=Q(
                    verification_status=Enterprise.VERIFICATION_NOT_VERIFIED
                )
            ),
            total_count=Count('pk', ),
        )


class ClientQuerySet(models.QuerySet):
    """Queryset class for `Client` model."""

    def has_lead_with_user(self, user):
        """Filter clients that attorney has lead with.

        If user is attorney, we filter queryset to return clients that
        attorney has a lead with.

        """
        if user.is_attorney:
            return self.filter(leads__attorney_id=user.pk)
        return self

    def has_matter_with_user(self, user, matter_statuses=None):
        """Filter clients that attorney has matter with.

        If user is attorney, we filter queryset to return clients with which
        attorney has a matter (with input statuses).

        If user is shared attorney or support, we filter queryset to return
        clients from shared with them matters (with input statuses).

        """
        from ...business.models import Matter

        if not matter_statuses:
            matter_statuses = (Matter.STATUS_OPEN, Matter.STATUS_CLOSE)

        if user.is_client:
            return self

        return self.filter(
            # filter clients which have matters with current user attorney
            Q(matters__attorney_id=user.pk) |
            # filter clients from shared matters with current user attorney or
            # support
            Q(matters__shared_links__user_id=user.pk),
            # restrict statuses
            matters__status__in=matter_statuses
        ).distinct()

    def invited_by_user(self, user):
        """Get clients that were invited by user."""
        return self.filter(user__invitations__inviter_id=user.pk).distinct()

    def user_clients(self, user):
        """Get attorneys clients.

        Attorney clients is clients that:
            Were invited by attorney
            Have matters with attorney
            Have leads with attorney
            Have shared matters with attorney

        """

        if not user.is_attorney:
            return self

        matter_filter = Q(matters__attorney_id=user.pk)
        lead_filter = Q(leads__attorney_id=user.pk)
        invite_filter = Q(user__invitations__inviter_id=user.pk)
        shared_matter_filter = Q(matters__shared_links__user_id=user.pk)

        return self.filter(
            matter_filter | shared_matter_filter | lead_filter | invite_filter
        ).distinct()


class SupportQuerySet(
    AbstractPaidObjectQuerySet, VerifiedRegistrationQuerySet
):
    """Queryset class for `Support` model."""


class UserStatisticsQuerySet(models.QuerySet):
    """Queryset class for `UserStatistics` model."""

    def for_period(
        self,
        user,
        start_date: datetime,
        end_date: datetime
    ):
        """Get stats for period of time."""
        return self.filter(
            user=user, created__gte=start_date, created__lte=end_date
        )

    def stats_count_for_tag(
        self,
        user,
        tag: str,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Get stats count for period of time by tag."""
        count = self.for_period(
            user=user, start_date=start_date, end_date=end_date
        ).filter(tag=tag).aggregate(Sum('count'))['count__sum']
        if not count:
            return 0
        return count
