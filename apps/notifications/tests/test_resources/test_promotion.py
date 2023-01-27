from ....promotion.factories import EventFactory
from ....users.models import Attorney, Client
from ...services import resources


class TestNewAttorneyEventNotificationResource:
    """Test `NewAttorneyEventNotificationResource`."""

    def test_get_recipients(
        self, attorney: Attorney, client: Client
    ):
        """Test get_recipients method."""
        instance = EventFactory(attorney=attorney)
        resource = resources.NewAttorneyEventNotificationResource(
            instance=instance
        )
        assert client.user in resource.get_recipients()
