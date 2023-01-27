from ...users.models import Attorney
from .. import factories


def test_is_participant(attorney: Attorney, other_attorney: Attorney):
    """Test GroupChat `is_participant` method."""
    chat_for_both = factories.GroupChatFactory(creator_id=attorney.pk)
    attorney_chat = factories.GroupChatFactory(creator_id=attorney.pk)

    chat_for_both.participants.add(other_attorney.pk)

    assert chat_for_both.is_participant(other_attorney.user)
    assert chat_for_both.is_participant(attorney.user)

    assert not attorney_chat.is_participant(other_attorney.user)
    # creator is a chat participant
    assert attorney_chat.is_participant(attorney.user)
