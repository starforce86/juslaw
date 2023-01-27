from ....social.factories import GroupChatFactory
from ....users.factories import AppUserWithAttorneyFactory
from ...services import resources


class TestNewNetworkResource:
    """Test `NewNetworkResource`."""

    def test_get_recipients(self):
        """Test get_recipients method for invited participants to network."""
        instance = GroupChatFactory()
        instance.participants.add(AppUserWithAttorneyFactory().pk)
        resource = resources.NewSingleGroupChatResource(
            instance=instance,
            invited=instance.participants.all().values_list('pk', flat=True),
            inviter=instance.creator
        )
        recipients = resource.get_recipients()
        assert instance.creator not in recipients
        for participant in instance.participants.all().exclude(
            pk=instance.creator_id
        ):
            assert participant in recipients
