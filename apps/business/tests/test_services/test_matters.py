from ....users.factories import SupportFactory
from ....users.models import AppUser, Attorney, Support
from ... import factories, models, services


def test_share_matter_by_invite(matter: models.Matter, mocker):
    """Test `share_matter_by_invite` service method.

    Check that new `invites` related to matter are generated and there is
    called a signal to send invitation.

    """
    send = mocker.patch(
        'apps.users.notifications.InviteNotification.send'
    )
    # check that matter has no `invitations` yet
    invitation_email = 'share-matter-test-email@test.com'
    assert not matter.invitations.filter(email=invitation_email).exists()
    services.share_matter_by_invite(
        matter.attorney.user,
        matter,
        title='Test',
        message='Test',
        emails=[invitation_email]
    )
    # check that new matter invitation is created
    invitation = matter.invitations.filter(email=invitation_email).first()
    assert invitation.title == 'Test'
    assert invitation.message == 'Test'
    assert invitation.email == 'share-matter-test-email@test.com'

    # check that invitation was really sent
    send.assert_called()


def test_share_matter_with_users_with_attorneys(
    matter: models.Matter, shared_attorney: Attorney, support: Support, mocker
):
    """Test `share_matter_with_users` service method with attorneys users type.

    Check that `MatterSharedWith` links would be created only for new
    users, already added before users and matter owner would be
    ignored, absent users would be removed. Also check that
    `SharedWithEmailNotification` notification will be sent.

    Check that `support` users in input data and `matter.shared_with` would be
    ignored.

    """
    shared_with_notification = mocker.patch(
        'apps.business.signals.new_matter_shared.send',
        return_value=None
    )
    already_shared = factories.MatterSharedWithFactory(matter=matter)
    # add already shared attorney that should be removed
    factories.MatterSharedWithFactory(matter=matter)
    owner = matter.attorney.user
    new = factories.AttorneyFactory().user
    new_support = SupportFactory().user

    services.share_matter_with_users(
        user=matter.attorney.user,
        matter=matter,
        title='Test',
        message='Test',
        users=[already_shared.user, owner, new, new_support],
        user_type=AppUser.USER_TYPE_ATTORNEY
    )

    user_ids = {
        already_shared.user_id, new.pk, support.pk,
        owner.pk, new_support.pk, shared_attorney.pk
    }
    expected = {already_shared.user_id, new.pk, support.pk}
    shared_user_ids = set(matter.shared_with.values_list('id', flat=True))
    assert user_ids & shared_user_ids == expected
    shared_with_notification.assert_called_once()


def test_share_matter_with_users_with_support(
    matter: models.Matter,
    shared_attorney: Attorney,
    support: Support,
    mocker
):
    """Test `share_matter_with_users` service method with support users type.

    Check that `MatterSharedWith` links would be created only for new
    users, already added before users and matter owner would be
    ignored, absent users would be removed. Also check that
    `SharedWithEmailNotification` notification will be sent.

    Check that `attorneys` users in input data and `matter.shared_with` would
    be ignored.

    """
    shared_with_notification = mocker.patch(
        'apps.business.signals.new_matter_shared.send',
        return_value=None
    )
    already_shared = factories.MatterSharedWithFactory(
        matter=matter, user=SupportFactory().user
    )
    # add already shared attorney that should be removed
    factories.MatterSharedWithFactory(
        matter=matter, user=SupportFactory().user
    )
    new = SupportFactory().user
    new_attorney = factories.AttorneyFactory().user

    services.share_matter_with_users(
        user=matter.attorney.user,
        matter=matter,
        title='Test',
        message='Test',
        users=[already_shared.user, new, new_attorney, support.user],
        user_type=AppUser.USER_TYPE_SUPPORT
    )
    user_ids = {
        already_shared.user_id, new.pk, support.pk, new_attorney.pk,
        shared_attorney.pk,
    }
    expected = {already_shared.user_id, new.pk, support.pk, shared_attorney.pk}
    shared_user_ids = set(matter.shared_with.values_list('id', flat=True))
    assert user_ids & shared_user_ids == expected
    shared_with_notification.assert_called_once()
