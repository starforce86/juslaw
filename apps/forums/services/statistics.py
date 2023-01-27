from ...forums import models
from ...users.models import Attorney

__all__ = (
    'get_attorney_statistics',
    'get_stats_for_dashboard',
)


def get_attorney_statistics(attorney: Attorney) -> dict:
    """Get attorney statistics for forums app."""
    opportunities_count = models.Topic.objects.opportunities(
        attorney.user
    ).count()

    return {
        'opportunities_count': opportunities_count,
    }


def get_stats_for_dashboard():
    """Collect forums stats for admin dashboard."""
    statistics = [
        {
            'stats_msg': 'Topics count',
            'stats': models.Topic.objects.all().count(),
        },
        {
            'stats_msg': 'Posts count',
            'stats': models.Post.objects.all().count(),
        },
    ]

    return statistics
