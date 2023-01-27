from ....users.models import Attorney, UserStatistic
from ...services import resources


class TestOpportunitiesNotificationResource:
    """Test `OpportunitiesNotificationResource`."""

    def test_get_recipients(
        self, attorney: Attorney,
    ):
        """Test get_recipients method."""
        instance = UserStatistic.objects.create(
            user=attorney.user,
            tag=UserStatistic.TAG_OPPORTUNITIES,
        )
        resource = resources.OpportunitiesNotificationResource(
            instance=instance
        )
        assert attorney.user in resource.get_recipients()
