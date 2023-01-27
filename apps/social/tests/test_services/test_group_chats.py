from ....users.factories import AppUserWithAttorneyFactory
from ...models import GroupChat
from ...services import add_participants_to_group_chat


def test_add_participants_to_group_chat(
    attorney_group_chat: GroupChat,
    mocker
):
    """Test add_participants_to_group_chat function"""
    added_to_group_chat_mock = mocker.patch(
        'apps.social.signals.added_to_group_chat.send'
    )
    inviter = attorney_group_chat.creator
    invited = AppUserWithAttorneyFactory()
    participants = (attorney_group_chat.creator, invited)
    add_participants_to_group_chat(
        group_chat=attorney_group_chat,
        participants=participants,
        inviter=inviter
    )
    added_to_group_chat_mock.assert_called_with(
        instance=attorney_group_chat,
        invited={invited.pk},
        inviter=inviter,
        sender=GroupChat,
        message=None,
    )
