from ...business import services as business_services
from ...forums import services as forums_services
from ...users import services as user_services


def get_apps_stats() -> dict:
    """Get Jus-Law app stats for admin dashboard and export."""
    stats = dict()
    stats['users_stats'] = user_services.get_stats_for_dashboard()
    stats['business_stats'] = business_services.get_stats_for_dashboard()
    stats['forums_stats'] = forums_services.get_stats_for_dashboard()
    return stats
