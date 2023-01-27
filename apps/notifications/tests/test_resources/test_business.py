from ....business.factories import (
    LeadFactory,
    MatterPostFactory,
    MatterSharedWithFactory,
)
from ....business.models import Matter, MatterTopic, VideoCall
from ....users.models import Attorney, Client
from ...factories import NotificationFactory
from ...services import resources


class TestNewChatResource:
    """Test `NewChatNotificationResource`."""

    def test_get_recipients_for_attorney(
        self,
        attorney: Attorney,
        other_client: Client,
    ):
        """Test get_recipients method for attorney case."""
        instance = LeadFactory(attorney=attorney, client=other_client)
        resource = resources.NewChatNotificationResource(
            instance=instance,
            created_by=other_client.user,
        )
        assert attorney.user in resource.get_recipients()

    def test_get_recipients_for_client(
        self,
        other_attorney: Attorney,
        client: Client,
    ):
        """Test get_recipients method for client case."""
        instance = LeadFactory(attorney=other_attorney, client=client)
        resource = resources.NewChatNotificationResource(
            instance=instance,
            created_by=other_attorney.user,
        )
        assert client.user in resource.get_recipients()


class TestNewMessageResource:
    """Test `NewMessageNotificationResource`."""

    def test_get_recipients_for_attorney(
        self,
        client: Client,
        attorney: Attorney,
        matter_topic: MatterTopic,
    ):
        """Test get_recipients method for attorney case."""
        instance = MatterPostFactory(
            topic=matter_topic,
            author=client.user
        )
        resource = resources.NewMessageNotificationResource(
            instance=instance
        )
        assert attorney.user in resource.get_recipients()

    def test_get_recipients_for_client(
        self,
        client: Client,
        attorney: Attorney,
        matter_topic: MatterTopic,
    ):
        """Test get_recipients method for client case."""
        instance = MatterPostFactory(
            topic=matter_topic,
            author=attorney.user
        )
        resource = resources.NewMessageNotificationResource(
            instance=instance
        )
        assert client.user in resource.get_recipients()


class TestNewVideoCallResource:
    """Test `NewVideoCallResource`."""

    def test_get_recipients_for_attorney(
        self,
        client: Client,
        attorney: Attorney,
        attorney_video_call: VideoCall,
    ):
        """Test get_recipients method for attorney case."""
        resource = resources.NewVideoCallResource(
            instance=attorney_video_call, caller=client
        )
        assert attorney.user in resource.get_recipients()
        assert client.user not in resource.get_recipients()

    def test_get_recipients_for_client(
        self,
        client: Client,
        attorney: Attorney,
        attorney_video_call: VideoCall,
    ):
        """Test get_recipients method for client case."""
        resource = resources.NewVideoCallResource(
            instance=attorney_video_call, caller=attorney
        )
        assert client.user in resource.get_recipients()
        assert attorney.user not in resource.get_recipients()


class TestMatterStatusUpdateNotificationResource:
    """Test `MatterStatusUpdateNotificationResource`."""

    def test_get_recipients(
        self, client: Client, matter: Matter,
    ):
        """Test get_recipients method."""
        resource = resources.MatterStatusUpdateNotificationResource(
            instance=matter,
            new_status=Matter.STATUS_REVOKED
        )
        assert client.user in resource.get_recipients()

    def test_get_web_notification_content(self, matter: Matter):
        """Check generated content when matter status is changed."""
        matter.status = Matter.STATUS_OPEN
        matter.save()
        notification = NotificationFactory(
            content_object=matter,
            extra_payload={'new_status': Matter.STATUS_REVOKED}
        )
        content = resources.MatterStatusUpdateNotificationResource \
            .get_web_notification_content(notification=notification)

        # change original matter status
        matter.activate()
        matter.save()

        # check that notification has old status
        assert content == f"Attorney changed status for matter '{matter}' " \
                          f"to {Matter.STATUS_REVOKED}."


class TestMatterSharedResource:
    """Test `MatterSharedResource`."""

    def test_get_recipients(self, matter: Matter):
        """Test get_recipients method."""
        matter_shared_with = MatterSharedWithFactory(matter=matter)
        resource = resources.MatterSharedResource(
            instance=matter_shared_with,
            inviter=matter.attorney,
            title='test',
            message='test'
        )
        assert matter_shared_with.user in resource.get_recipients()
