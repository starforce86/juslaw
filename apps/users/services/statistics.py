from datetime import datetime
from functools import partial

import arrow

from ...business import services as business_services
from ...documents import services as documents_services
from ...forums import services as forums_services
from ...users import models

__all__ = (
    'get_attorney_statistics',
    'get_attorney_period_statistic',
    'get_stats_for_time_period_by_tag',
    'get_stats_for_dashboard',
    'create_stat',
)


def get_attorney_statistics(attorney: models.Attorney) -> dict:
    """Get attorney statistics from all apps.

    Current attorney statistics is a statistics for current period of time.
        Current attorney statistics includes:
            Count of active leads,
            Count of active matters,
            Count of documents,
            Count of opportunities

    """
    statistics = {}
    statistics.update(business_services.get_attorney_statistics(attorney))
    statistics.update(documents_services.get_attorney_statistics(attorney))
    statistics.update(forums_services.get_attorney_statistics(attorney))
    return statistics


def get_attorney_period_statistic(
    attorney: models.Attorney,
    start: datetime,
    end: datetime,
    time_frame: str = 'month'
) -> dict:
    """Get attorney statistics for period of time divided by time frame.

    Period attorney statistics is a statistics for selected period of time,
    where some of them (time_billed for now) divided by time frame.
    Period attorney statistics includes:
        Amount of billed time,
        Count of active leads for period of time,
        Count of active matters for period of time,
        Count of opportunities for period of time,
        Count of converted leads for period of time,

    """
    statistics = {}
    statistics_tags_map = {
        'opportunities_stats': models.UserStatistic.TAG_OPPORTUNITIES,
        'active_leads_stats': models.UserStatistic.TAG_ACTIVE_LEAD,
        'active_matters_stats': models.UserStatistic.TAG_OPEN_MATTER,
        'converted_lead': models.UserStatistic.TAG_CONVERTED_LEAD,
    }
    get_stats = partial(
        get_stats_for_time_period_by_tag,
        user=attorney.user,
        start=start,
        end=end,
        time_frame=time_frame
    )

    for key, tag in statistics_tags_map.items():
        statistics[key] = get_stats(tag=tag)

    statistics.update(
        business_services.get_attorney_period_statistic(
            attorney=attorney, start=start, end=end, time_frame=time_frame
        )
    )

    return statistics


def get_stats_for_time_period_by_tag(
    user: models.AppUser,
    start: datetime,
    end: datetime,
    tag: str,
    time_frame: str = 'month',
) -> dict:
    """Get user stats by tag for time period divided by time frame."""
    stats = []
    total_sum = 0
    start = arrow.get(start)
    end = arrow.get(end)
    for range_date in list(arrow.Arrow.range(time_frame, start, end)):
        # Calculate amount of matters for period of time
        count = models.UserStatistic.objects.stats_count_for_tag(
            user=user,
            start_date=range_date.floor(time_frame).datetime,
            end_date=range_date.ceil(time_frame).datetime,
            tag=tag
        )
        total_sum += count
        stats.append(
            {
                'date': range_date.datetime,
                'count': count
            },
        )

    return {
        'total_sum': total_sum,
        'stats': stats,
    }


def create_stat(user, tag: str, count: int = 1) -> models.UserStatistic:
    """Create statistic entry for user."""
    return models.UserStatistic.objects.create(user=user, tag=tag, count=count)


def get_stats_for_dashboard() -> list:
    """Collect user stats for admin dashboard."""
    attorney_stats = models.Attorney.objects.aggregate_count_stats()
    paralegal_stats = models.Paralegal.objects.aggregate_count_stats()
    enterprise_stats = models.Enterprise.objects.aggregate_count_stats()
    clients_count = models.Client.objects.all().count()
    total = attorney_stats['total_count'] + clients_count
    statistics = [
        {
            'stats_msg': 'Verified attorneys',
            'stats': attorney_stats['verified_count'],
        },
        {
            'stats_msg': 'Awaiting verification attorneys',
            'stats': attorney_stats['not_verified_count'],
        },
        {
            'stats_msg': 'Attorneys',
            'stats': attorney_stats['total_count'],
        },
        {
            'stats_msg': 'Verified paralegals',
            'stats': paralegal_stats['verified_count'],
        },
        {
            'stats_msg': 'Awaiting verification paralegals',
            'stats': paralegal_stats['not_verified_count'],
        },
        {
            'stats_msg': 'Paralegals',
            'stats': paralegal_stats['total_count'],
        },
        {
            'stats_msg': 'Verified enterprise',
            'stats': enterprise_stats['verified_count'],
        },
        {
            'stats_msg': 'Awaiting verification enterprise',
            'stats': enterprise_stats['not_verified_count'],
        },
        {
            'stats_msg': 'Enterprise',
            'stats': enterprise_stats['total_count'],
        },
        {
            'stats_msg': 'Clients',
            'stats': clients_count,
        },
        {
            'stats_msg': 'Total',
            'stats': total,
        }

    ]

    return statistics
