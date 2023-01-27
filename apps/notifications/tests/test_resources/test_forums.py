from ....forums.factories import PostFactory
from ....forums.models import Topic
from ....users.models import Attorney, Client
from ...services import resources


class TestNewPostNotificationResource:
    """Test `NewPostNotificationResource`."""

    def test_get_recipients(
        self,
        attorney: Attorney,
        client: Client,
        followed_topic: Topic,
    ):
        """Test get_recipients method for both attorney and client."""
        instance = PostFactory(topic=followed_topic)
        resource = resources.NewPostNotificationResource(
            instance=instance
        )
        recipients = resource.get_recipients()
        assert attorney.user in recipients
        assert client.user in recipients


class TestNewAttorneyPostNotificationResource:
    """Test `NewAttorneyPostNotificationResource`."""

    def test_get_recipients(
        self, attorney: Attorney, client: Client
    ):
        """Test get_recipients method."""
        instance = PostFactory(author=attorney.user)
        resource = resources.NewAttorneyPostNotificationResource(
            instance=instance
        )
        assert client.user in resource.get_recipients()
