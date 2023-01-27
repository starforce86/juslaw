from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.test import override_settings

import pytest

from ..factories import (
    AppUserFactory,
    AttorneyFactory,
    AttorneyVerifiedFactory,
    ClientFactory,
    InviteFactory,
    SupportFactory,
    SupportVerifiedFactory,
)
from ..models import AppUser, Attorney, Client, Invite, Support
from ..models.clients import AbstractClient


@pytest.fixture(scope='function')
def support() -> Support:
    """Create support for model testing."""
    return SupportFactory()


@pytest.fixture(scope='function')
def verified_support() -> Support:
    """Create verified support for model testing."""
    return SupportVerifiedFactory()


@pytest.fixture(scope='function')
def attorney() -> Attorney:
    """Create attorney for model testing."""
    return AttorneyFactory()


@pytest.fixture(scope='function')
def verified_attorney() -> Attorney:
    """Create attorney for model testing."""
    return AttorneyVerifiedFactory()


@pytest.fixture(scope='function')
def client() -> Client:
    """Create client for model testing."""
    return ClientFactory()


@pytest.fixture(scope='function')
def invite() -> Invite:
    """Create invite for model testing."""
    return InviteFactory()


@pytest.fixture
def user(
    request,
    client: Client,
    attorney: Attorney,
    support: Support,
) -> AppUser:
    """Fixture to use fixtures in decorator parametrize for AppUser object."""
    mapping = {
        'client': client.user,
        'attorney': attorney.user,
        'support': support.user,
    }
    return mapping.get(request.param)


class TestAttorneyModel:
    """Test Attorney model."""

    def test_verification_restriction(self, attorney: Attorney):
        """Test that just created attorney can't be authenticated."""
        password = 'test_verification'
        attorney.user.set_password(password)

        attorney.user.save()
        user = authenticate(email=attorney.email, password=password)

        assert not user

    @override_settings(STRIPE_ENABLED=False)
    def test_verification_authentication(self, attorney: Attorney):
        """Test that after verification attorney can be authenticated."""
        password = 'test_verification'
        attorney.user.set_password('test_verification')
        attorney.user.save()

        attorney.verify()
        user = authenticate(email=attorney.email, password=password)

        assert user

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=('client', 'support'),
        indirect=True
    )
    def test_clean_user(self, attorney: Attorney, user: AppUser):
        """Test that attorney can't be another user type at the same time."""
        attorney.user = user

        with pytest.raises(ValidationError):
            attorney.clean()

    @override_settings(STRIPE_ENABLED=False)
    @patch('apps.users.notifications.VerificationApprovedEmailNotification')
    def test_verify_by_admin(self, email_mock, attorney: Attorney):
        """Test that verify_by_admin works and notification email is sent."""
        attorney.verify_by_admin()

        # Check that attorney is now verified and user profile is active
        attorney.refresh_from_db()
        assert attorney.is_verified

        attorney.user.refresh_from_db()
        assert attorney.user.is_active

        # Check attorney was notified about verification
        email_mock.assert_called_once_with(attorney.user)
        email_mock().send.assert_called_once()

    @patch('apps.users.notifications.VerificationDeclinedEmailNotification')
    def test_decline_by_admin(self, email_mock, verified_attorney: Attorney):
        """Test that decline_by_admin works and notification email is sent."""
        verified_attorney.decline_by_admin()

        # Check that attorney is not verified and user profile is active
        verified_attorney.refresh_from_db()
        assert not verified_attorney.is_verified

        verified_attorney.user.refresh_from_db()
        assert not verified_attorney.user.is_active

        # Check attorney was notified about verification decline
        email_mock.assert_called_once_with(verified_attorney.user)
        email_mock().send.assert_called_once()


class TestAbstractModel:
    """Test AbstractClient model."""

    def test_clean_organisation_name_for_firm_user(self):
        """Test that firm client must have `organization_name`."""
        client = AbstractClient(client_type=AbstractClient.FIRM_TYPE)

        with pytest.raises(ValidationError):
            client.clean()

    def test_clean_organisation_name_for_individual_user(self):
        """Test that individual client can't have `organization_name`."""

        client = AbstractClient(
            client_type=AbstractClient.INDIVIDUAL_TYPE,
            organization_name='organization_name'
        )

        with pytest.raises(ValidationError):
            client.clean()


class TestClientModel:
    """Test Client model."""

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=('attorney', 'support'),
        indirect=True
    )
    def test_clean_user(self, client: Client, user: AppUser):
        """Test that client can't be another user type at the same time."""
        client.user = user

        with pytest.raises(ValidationError):
            client.clean()


class TestSupportModel:
    """Test Support model."""

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=('attorney', 'client'),
        indirect=True
    )
    def test_clean_user(self, support: Support, user: AppUser):
        """Test that support can't be another user type at the same time."""
        support.user = user

        with pytest.raises(ValidationError):
            support.clean()

    @override_settings(STRIPE_ENABLED=False)
    @patch('apps.users.notifications.VerificationApprovedEmailNotification')
    def test_verify_by_admin(self, email_mock, support: Support):
        """Test that verify_by_admin works and notification email is sent."""
        support.verify_by_admin()

        # Check that support is now verified and user profile is active
        support.refresh_from_db()
        assert support.is_verified

        support.user.refresh_from_db()
        assert support.user.is_active

        # Check support user was notified about verification
        email_mock.assert_called_once_with(support.user)
        email_mock().send.assert_called_once()

    @patch('apps.users.notifications.VerificationDeclinedEmailNotification')
    def test_decline_by_admin(self, email_mock, verified_support: Support):
        """Test that decline_by_admin works and notification email is sent."""
        verified_support.decline_by_admin()

        # Check that support user is not verified and user profile is inactive
        verified_support.refresh_from_db()
        assert not verified_support.is_verified

        verified_support.user.refresh_from_db()
        assert not verified_support.user.is_active

        # Check support user was notified about verification decline
        email_mock.assert_called_once_with(verified_support.user)
        email_mock().send.assert_called_once()


class TestInviteModel:
    """Test Invite model."""

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney'
        ),
        indirect=True
    )
    def test_clean_email(self, invite: Invite, user: AppUser):
        """Test that new invite can't be addressed to registered user."""
        invite.email = user.email

        with pytest.raises(ValidationError):
            invite.clean()

        # Check case insensitivity
        invite.email = user.email.upper()

        with pytest.raises(ValidationError):
            invite.clean()


class TestAppUser:
    """Test AppUser model."""

    def test_is_attorney(
        self, attorney: Attorney, client: Client, support: Support,
        staff: AppUser
    ):
        """Test `is_attorney` method"""
        assert attorney.user.is_attorney
        assert not client.user.is_attorney
        assert not support.user.is_attorney
        assert not staff.is_attorney

    def test_is_client(
        self, attorney: Attorney, client: Client, support: Support,
        staff: AppUser
    ):
        """Test `is_client` method"""
        assert client.user.is_client
        assert not attorney.user.is_client
        assert not support.user.is_client
        assert not staff.is_client

    def test_is_support(
        self, attorney: Attorney, client: Client, support: Support,
        staff: AppUser
    ):
        """Test `is_support` method"""
        assert support.user.is_support
        assert not attorney.user.is_support
        assert not client.user.is_support
        assert not staff.is_support

    def test_user_type(
        self, attorney: Attorney, client: Client, support: Support,
        staff: AppUser
    ):
        """Test `user_type` method"""
        assert client.user.user_type == 'client'
        assert attorney.user.user_type == 'attorney'
        assert support.user.user_type == 'support'
        assert staff.user_type == 'staff'

    def test_is_developer(self, staff: AppUser):
        """Test `is_developer` method"""
        assert not staff.is_developer
        assert AppUserFactory(email='root@root.ru').is_developer
        assert AppUserFactory(email=settings.ADMINS[0][1]).is_developer
