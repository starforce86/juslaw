import json
from unittest.mock import MagicMock, patch

from django.urls import reverse_lazy

from rest_framework.test import APIClient

from ....users.factories import (
    AppUserWithAttorneyFactory,
    AttorneyFactory,
    InviteFactory,
)
from ....users.models import Client
from ... import factories, models


def get_lead_list_url():
    """Get url for lead creation."""
    return reverse_lazy('v1:leads-list')


@patch('apps.business.signals.matters.matter_status_update')
def test_matter_status_update_signal(signal_mock: MagicMock):
    """Test that `matter_status_update` signal works."""
    matter: models.Matter = factories.MatterFactory(
        status=models.Matter.STATUS_OPEN
    )
    matter.revoke()
    signal_mock.send.assert_called_with(
        sender=matter.__class__,
        instance=matter,
        new_status=models.Matter.STATUS_REVOKED
    )


@patch('apps.business.api.serializers.matter.new_lead')
def test_new_lead_signal(
    signal_mock: MagicMock,
    auth_client_api: APIClient,
    client: Client
):
    """Test that `new_lead` signal works."""
    lead_json = {
        'client': client.pk,
        'attorney': AttorneyFactory().pk
    }
    url = get_lead_list_url()
    response = auth_client_api.post(url, lead_json)
    response_data = json.loads(response.content)
    instance = models.Lead.objects.get(pk=response_data['id'])
    signal_mock.send.assert_called_with(
        sender=instance.__class__,
        instance=instance,
        created_by=client.user
    )


def test_send_shared_matter_notification(
    matter: models.Matter, another_matter: models.Matter, mocker
):
    """Check that `send_shared_matter_notification` signal works correctly.

    Check that when user invited from `share matter` is registered and verified
    in app he would get notification that matter was shared with him and matter
    would be really shared with him.

    """
    shared_with_notification = mocker.patch(
        'apps.business.signals.new_matter_shared.send',
        return_value=None
    )
    inviter = AppUserWithAttorneyFactory()
    email = 'test@test.com'
    invite_for_matter_1 = InviteFactory(
        matter=matter, title='Test 1', message='Test 1', inviter=inviter,
        email=email
    )
    invite_for_matter_2 = InviteFactory(
        matter=matter, title='Test 2', message='Test 2', inviter=inviter,
        email=email
    )
    invite_for_other_matter = InviteFactory(
        matter=another_matter, title='Test 3', message='Test 3',
        inviter=inviter, email=email
    )

    # check that both matters have no `shared_with` users with email
    assert not matter.shared_with.filter(email__iexact=email).exists()
    assert not another_matter.shared_with.filter(email__iexact=email).exists()

    user = AppUserWithAttorneyFactory(email=email)
    user.attorney.verify_by_admin()

    # check that registered user is added to invite
    for invite in [invite_for_matter_1, invite_for_matter_2,
                   invite_for_other_matter]:  # noqa
        invite.refresh_from_db()
        assert invite.user == user

    # check that now user with `email` exists in `shared_with` for both matters
    assert matter.shared_with.filter(email__iexact=email).exists()
    assert another_matter.shared_with.filter(email__iexact=email).exists()

    # check that there were created only 2 notifications (latest matter's one
    # and for another_matter)
    assert shared_with_notification.call_count == 2
