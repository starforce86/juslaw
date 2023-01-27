from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from ....users.factories import AttorneyFactory
from ....users.models import AppUser
from ... import models
from ...api import serializers
from ...factories import GroupChatFactory


def get_list_url():
    """Get url for group chat creation and list retrieval."""
    return reverse_lazy('v1:group_chats-list')


def get_detail_url(group_chat: models.GroupChat):
    """Get url for group chat editing and retrieval."""
    return reverse_lazy(
        'v1:group_chats-detail', kwargs={'pk': group_chat.pk}
    )


def get_add_participant_url(group_chat: models.GroupChat):
    """Get url for adding participants to group chat ."""
    return reverse_lazy(
        'v1:group_chats-add-participants', kwargs={'pk': group_chat.pk}
    )


class TestAuthUserAPI:
    """Test group chat api for auth users.

    This api can be used only by attorneys.

    """

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_200_OK),
        ),
        indirect=True
    )
    def test_get_list_group_chat(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code: int,
    ):
        """Test that attorney can get group chats, but clients can't."""
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status_code

        if user.is_attorney:
            group_chats = models.GroupChat.objects.available_for_user(
                user=user
            )
            assert group_chats.count() == response.data['count']
            for group_chat_data in response.data['results']:
                group_chats.get(pk=group_chat_data['id'])

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_200_OK),
        ),
        indirect=True
    )
    def test_retrieve_group_chat(
        self,
        api_client: APIClient,
        user: AppUser,
        attorney_group_chat: models.GroupChat,
        status_code: int,
    ):
        """Test that attorney can get group chat details, but client can't."""
        url = get_detail_url(attorney_group_chat)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status_code

        if user.is_attorney:
            models.GroupChat.objects.available_for_user(user=user).get(
                pk=response.data['id']
            )

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_201_CREATED),
        ),
        indirect=True
    )
    def test_create_group_chat(
        self,
        api_client: APIClient,
        user: AppUser,
        attorney_group_chat: models.GroupChat,
        status_code: int,
    ):
        """Test that attorney can create group chat, but client can't."""
        group_chat_json = serializers.GroupChatSerializer(
            instance=attorney_group_chat
        ).data
        group_chat_json['title'] = 'test group_chat creation'
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.post(
            url, group_chat_json
        )

        assert response.status_code == status_code

        if user.is_attorney:
            # Check that new group chat appeared in db
            group_chat = models.GroupChat.objects.available_for_user(
                user=user).get(
                pk=response.data['id']
            )
            # Check that attorney is also participant
            assert user in group_chat.participants.all()

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_200_OK),
            ('participant', status.HTTP_200_OK),
        ),
        indirect=True,
    )
    def test_edit_group_chat(
        self,
        api_client: APIClient,
        user: AppUser,
        attorney_group_chat: models.GroupChat,
        status_code: int,
    ):
        """Test that attorney can edit group chat, but client can't."""
        group_chat_json = serializers.GroupChatSerializer(
            instance=attorney_group_chat
        ).data
        title = 'test group_chat editing'
        group_chat_json['title'] = title
        url = get_detail_url(attorney_group_chat)

        api_client.force_authenticate(user=user)
        response = api_client.put(
            url, group_chat_json
        )

        assert response.status_code == status_code

        if user.is_attorney:
            # Check that group chat was updated in db
            attorney_group_chat.refresh_from_db()
            assert attorney_group_chat.title == title

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', status.HTTP_403_FORBIDDEN),
            ('other_attorney', status.HTTP_404_NOT_FOUND),
        ),
        indirect=True
    )
    def test_edit_foreign_group_chat(
        self,
        api_client: APIClient,
        user: AppUser,
        attorney_group_chat: models.GroupChat,
        status_code: int
    ):
        """Test that users can't edit group chat of other user."""
        group_chat_json = serializers.GroupChatSerializer(
            instance=attorney_group_chat
        ).data
        url = get_detail_url(attorney_group_chat)

        api_client.force_authenticate(user=user)
        response = api_client.put(
            url, group_chat_json
        )

        assert response.status_code == status_code

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_200_OK),
            ('participant', status.HTTP_200_OK),
            ('other_attorney', status.HTTP_404_NOT_FOUND),
        ),
        indirect=True
    )
    def test_add_participants(
        self,
        api_client: APIClient,
        user: AppUser,
        attorney_group_chat: models.GroupChat,
        status_code: int
    ):
        """Test that attorney can invite to group chat, but clients can't."""
        url = get_add_participant_url(attorney_group_chat)
        attorney = AttorneyFactory()
        json_request = dict(
            participants=[attorney.pk],
            message='Test invite'
        )

        api_client.force_authenticate(user=user)
        response = api_client.post(url, json_request)

        assert response.status_code == status_code

        if response.status_code == status.HTTP_200_OK:
            # Check that attorney was added to participants
            attorney_group_chat.refresh_from_db()
            assert attorney.user in attorney_group_chat.participants.all()

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('attorney', status.HTTP_204_NO_CONTENT),
            ('other_attorney', status.HTTP_204_NO_CONTENT),
        ),
        indirect=True
    )
    def test_leave(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code: int
    ):
        """Test that attorney can leave group chat."""
        group_chat = GroupChatFactory()
        group_chat.participants.add(user.pk)
        assert user in group_chat.participants.all()

        url = get_detail_url(group_chat)

        api_client.force_authenticate(user=user)
        response = api_client.delete(f'{url}leave/',)

        assert response.status_code == status_code

        # Check that attorney was removed from participants
        group_chat.refresh_from_db()
        assert user not in group_chat.participants.all()
