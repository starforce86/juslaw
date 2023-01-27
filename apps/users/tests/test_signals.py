from unittest.mock import MagicMock, patch

import pytest

from ...notifications.models import NotificationSetting, NotificationType
from .. import factories, models


@patch('apps.users.signals.new_opportunities_for_attorney')
def test_new_opportunities_for_attorney_signal(
    signal_mock: MagicMock,
    attorney: models.Attorney,
):
    """Test that `new_opportunities_for_attorney` signal works."""
    instance = models.UserStatistic.objects.create(
        user=attorney.user,
        tag=models.UserStatistic.TAG_OPPORTUNITIES,
    )
    signal_mock.send.assert_called_with(
        sender=instance.__class__, instance=instance
    )


@pytest.mark.parametrize(
    argnames='user_factory,',
    argvalues=(factories.AttorneyFactory, factories.SupportFactory),
)
@patch('apps.users.notifications.RegisterUserNotification')
def test_new_support_profile(email_mock, user_factory):
    """Test that `new_user_profile_for_verification` signal works."""
    instance = user_factory()

    # Check that user profile is not active
    instance.user.refresh_from_db()
    assert not instance.user.is_active

    # Check admin were notified about new user
    email_mock.assert_called_once_with(instance.user)
    email_mock().send.assert_called_once()


@pytest.mark.parametrize(
    argnames='user_factory,',
    argvalues=(factories.AttorneyFactory, factories.SupportFactory),
)
def test_new_user_template_folder(user_factory):
    """Test that `new_user_template_folder` signal works."""
    instance = user_factory()

    # Check that template folder was created
    instance.user.refresh_from_db()
    assert instance.user.folders.filter(is_template=True).count() == 1


@patch('apps.users.notifications.InviteNotification')
def test_send_invitation_mail_signal(email_mock, attorney: models.Attorney):
    """Test that `send_invitation_mail` signal works."""
    invite = factories.InviteFactory(inviter=attorney.user)

    # Check that invitation email was sent
    email_mock.assert_called_once_with(invite=invite)
    email_mock().send.assert_called_once()


@patch('apps.users.notifications.RegisteredClientNotification')
def test_inform_inviter_about_client_signal(
    email_mock, attorney: models.Attorney
):
    """Test that `inform_inviter_about_client` signal works."""
    invite = factories.InviteFactory(inviter=attorney.user)
    factories.ClientFactory(user__email=invite.email)

    # Check that notification email was sent
    email_mock.assert_called_once_with(invite=invite)
    email_mock().send.assert_called_once()


def test_set_link_to_user_in_invites_signal():
    """Test that `set_link_to_user_in_invites` signal works."""
    email = 'Test-Set-Link-To-User@text.com'

    invite = factories.InviteFactory(email=email)
    invite_upper = factories.InviteFactory(email=email.upper())
    invite_lower = factories.InviteFactory(email=email.lower())

    # Register new user
    factories.AppUserFactory(email=email)

    invites_without_user = models.Invite.objects.without_user()

    # Check that invites won't appear as active(client field was set)
    assert invite not in invites_without_user
    assert invite_upper not in invites_without_user
    assert invite_lower not in invites_without_user


@pytest.mark.parametrize(
    argnames='factory',
    argvalues=(
        factories.AttorneyFactory,
        factories.ClientFactory,
        factories.SupportFactory
    ),
)
def test_enable_notifications(factory):
    """Test `enable_notifications` signal for new attorney, client and support.
    """
    new_user = factory()
    user = new_user.user
    settings = NotificationSetting.objects.filter(user=user)
    notification_types_count = NotificationType.objects.user_types(
        user=user
    ).count()

    assert notification_types_count == settings.count()
    # Check that settings were set correctly
    enabled_settings = settings.filter(by_email=True, by_push=True)
    assert settings.count() == enabled_settings.count()
