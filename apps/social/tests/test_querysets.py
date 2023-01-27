from ...users.models import Attorney
from .. import factories, models


class TestGroupChatQuerySet:
    """Tests for `GroupChatQuerySet` methods."""

    def available_for_user(
        self,
        attorney: Attorney,
        other_attorney: Attorney,
    ):
        """Test `available_for_user` qs method."""
        both_attorneys_in_chat = factories.GroupChatFactory(
            creator_id=attorney.pk
        )
        both_attorneys_in_chat.participants.add(other_attorney.pk)
        one_attorney_in_chat = factories.GroupChatFactory(
            creator_id=attorney.pk
        )
        attorney_group_chats = models.GroupChat.objects.available_for_user(
            user=attorney.user
        )
        assert both_attorneys_in_chat in attorney_group_chats
        assert one_attorney_in_chat in attorney_group_chats

        other_attorney_group_chats = models.GroupChat.objects.\
            available_for_user(user=other_attorney.user)
        assert both_attorneys_in_chat in other_attorney_group_chats
        # Other attorney is not creator neither is participant
        assert one_attorney_in_chat not in other_attorney_group_chats
