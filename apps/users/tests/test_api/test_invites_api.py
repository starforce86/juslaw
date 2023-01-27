from django.core import mail
from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import (
    CONFLICT,
    CREATED,
    FORBIDDEN,
    NO_CONTENT,
    OK,
    UNAUTHORIZED,
)

from apps.business.models import Matter

from ...api.serializers import InviteSerializer
from ...factories import InviteFactory
from ...models import AppUser, Attorney, Invite


@pytest.fixture(scope='module')
def invite(django_db_blocker, attorney: Attorney) -> Invite:
    """Create invite for testing."""
    with django_db_blocker.unblock():
        return InviteFactory(inviter=attorney.user)


def get_list_url():
    """Get url for invites list retrieval."""
    return reverse_lazy('v1:invites-list')


def get_detail_url(invite: Invite):
    """Get url for invite retrieval."""
    return reverse_lazy('v1:invites-detail', kwargs={'pk': invite.pk})


def get_invite_resend_url(invite: Invite):
    """Get url for invite resending."""
    return reverse_lazy('v1:invites-resend', kwargs={'pk': invite.pk})


class TestInviteAPI:
    """Test invites api."""
    users_status_codes_params = (
        ('anonymous', UNAUTHORIZED),
        ('client', FORBIDDEN),
        ('attorney', OK),
    )

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=users_status_codes_params,
        indirect=True
    )
    def test_get_list(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code,
        matter: Matter
    ):
        """Test that only attorney can get list of invites."""
        if user:
            # create invite generated from matter - should be returned
            InviteFactory(inviter=user, matter=matter)
            # create invite with `imported` type - shouldn't be returned
            InviteFactory(inviter=user, type=Invite.TYPE_IMPORTED)

        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status_code

        # Check that correct invites have been returned by api
        if user and user.is_attorney:
            attorney_invites = Invite.objects.without_user() \
                .only_invited_type().filter(inviter=user)
            for invite_data in response.data['results']:
                attorney_invites.get(pk=invite_data['uuid'])

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'anonymous',
            'client',
            'attorney',
        ),
        indirect=True
    )
    def test_retrieve_invite(
        self, api_client: APIClient, user: AppUser, invite: Invite
    ):
        """Test that anybody can get invitation from api."""
        url = get_detail_url(invite=invite)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == OK
        Invite.objects.get(pk=response.data['uuid'])

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('anonymous', UNAUTHORIZED),
            ('client', FORBIDDEN),
            ('attorney', CREATED),
        ),
        indirect=True
    )
    def test_create_invite(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code,
        invite: Invite
    ):
        """Test that only attorney can send invite."""
        data = InviteSerializer(instance=invite).data
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.post(url, data)

        assert response.status_code == status_code

        # Check that invite was created
        if user and user.is_attorney:
            Invite.objects.get(pk=response.data['uuid'])

    def test_create_invite_with_registered_user(
        self, auth_attorney_api: APIClient, invite: Invite
    ):
        """Test that attorney can't create invite for registered user."""
        data = InviteSerializer(instance=invite).data
        registered_user = AppUser.objects.first()
        data['email'] = registered_user.email
        url = get_list_url()

        response = auth_attorney_api.post(url, data)
        assert response.status_code == CONFLICT

        # Check that api returned correct data about registered user
        assert int(response.data['id']) == registered_user.pk
        assert str(response.data['user_type']) == registered_user.user_type

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=users_status_codes_params,
        indirect=True
    )
    def test_update_invite(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code,
        invite: Invite
    ):
        """Test that only attorney can update invites."""
        data = InviteSerializer(instance=invite).data
        data['message'] = 'test invite editing'
        url = get_detail_url(invite=invite)

        api_client.force_authenticate(user=user)
        response = api_client.put(url, data)

        assert response.status_code == status_code

        # Check that invite was updated
        if user and user.is_attorney:
            invite.refresh_from_db()
            assert invite.message == data['message']

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('anonymous', UNAUTHORIZED),
            ('client', FORBIDDEN),
            ('attorney', NO_CONTENT),
        ),
        indirect=True
    )
    def test_resend_invite(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code,
        invite: Invite
    ):
        """Test that only attorney can resend invites."""
        url = get_invite_resend_url(invite=invite)

        api_client.force_authenticate(user=user)
        response = api_client.post(url)

        assert response.status_code == status_code

        # Check that invite was resent
        if user and user.is_attorney:
            subject = f'Jus-Law - You have been invited by {invite.inviter}'
            filtered_inbox = [
                email for email in mail.outbox
                if email.subject == subject and email.to == [invite.email]
            ]
            assert len(filtered_inbox) == 1
