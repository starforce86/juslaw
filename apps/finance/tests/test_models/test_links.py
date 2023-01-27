from datetime import datetime, timedelta
from typing import Union

from django.utils import timezone

import pytest

from apps.finance import models

pytestmark = pytest.mark.django_db


class TestFinanceProfileModel:
    """Tests for `FinanceProfile` model methods."""

    def test_send_verified_email_not_verified(
        self, finance_profile: models.FinanceProfile, mocker
    ):
        """Check `send_verified_email` method works correctly.

        Check that when `send_verified_email` method is called for not verified
        `account` - no email messages are sent

        """
        mocker.patch('apps.finance.models.AccountProxy.is_verified', False)
        send = mocker.patch('libs.notifications.email.EmailNotification.send')
        finance_profile.verified_email_sent = None
        finance_profile.save()

        finance_profile.send_verified_email()
        send.assert_not_called()

    def test_send_verified_email_already_sent(
        self, finance_profile: models.FinanceProfile, mocker
    ):
        """Check `send_verified_email` method works correctly.

        Check that when `send_verified_email` method is called for verified
        `account` for which `verification` email was already sent - no email
        messages are sent

        """
        mocker.patch('apps.finance.models.AccountProxy.is_verified', True)
        send = mocker.patch('libs.notifications.email.EmailNotification.send')
        finance_profile.verified_email_sent = timezone.now()
        finance_profile.save()

        finance_profile.send_verified_email()
        send.assert_not_called()

    def test_send_verified_email(
        self, finance_profile: models.FinanceProfile, mocker
    ):
        """Check `send_verified_email` method works correctly.

        Check that when `send_verified_email` method is called for verified
        `account` for which `verification` email wasn't sent yet - email
        message should be sent sent and corresponding fields should be updated.

        """
        mocker.patch('apps.finance.models.AccountProxy.is_verified', True)
        mocker.patch(
            'apps.finance.models.AccountProxy.login_url',
            'http://test.com'
        )
        send = mocker.patch(
            'libs.notifications.email.EmailNotification.send',
            return_value=True
        )
        finance_profile.verified_email_sent = None
        finance_profile.not_verified_email_sent = timezone.now()
        finance_profile.save()

        finance_profile.send_verified_email()
        finance_profile.refresh_from_db()
        send.assert_called()
        assert finance_profile.verified_email_sent is not None
        assert finance_profile.not_verified_email_sent is None

    def test_send_not_verified_email_verified(
        self, finance_profile: models.FinanceProfile, mocker
    ):
        """Check `send_not_verified_email` method works correctly.

        Check that when `send_not_verified_email` method is called for verified
        `account` - no email messages are sent

        """
        mocker.patch('apps.finance.models.AccountProxy.is_verified', True)
        send = mocker.patch('libs.notifications.email.EmailNotification.send')
        finance_profile.not_verified_email_sent = None
        finance_profile.save()

        finance_profile.send_not_verified_email()
        send.assert_not_called()

    def test_send_not_verified_email_already_sent_recently(
        self, finance_profile: models.FinanceProfile, mocker
    ):
        """Check `send_verified_email` method works correctly.

        Check that when `send_not_verified_email` method is called for not
        verified `account` for which `verification` email was already sent
        recently (less then 1 day ago) - no email messages are sent.

        """
        mocker.patch('apps.finance.models.AccountProxy.is_verified', False)
        send = mocker.patch('libs.notifications.email.EmailNotification.send')
        finance_profile.not_verified_email_sent = timezone.now() - \
            timedelta(hours=23)
        finance_profile.save()

        finance_profile.send_not_verified_email()
        send.assert_not_called()

    @pytest.mark.parametrize(
        argnames='not_verified_email_sent',
        argvalues=(
            timezone.now() - models.FinanceProfile.SEND_EMAIL_INTERVAL,
            None
        )
    )
    def test_send_not_verified_email(
        self, finance_profile: models.FinanceProfile,
        not_verified_email_sent: Union[datetime, None], mocker
    ):
        """Check `send_verified_email` method works correctly.

        Check that when `send_not_verified_email` method is called for not
        verified `account` for which `verification` email was already sent
        long time ago (more then 1 day ago) or haven't been sent yet - email
        message should be sent.

        """
        mocker.patch('apps.finance.models.AccountProxy.is_verified', False)
        mocker.patch(
            'apps.finance.models.AccountProxy.login_url',
            'http://test.com'
        )
        send = mocker.patch('libs.notifications.email.EmailNotification.send')
        finance_profile.not_verified_email_sent = not_verified_email_sent
        finance_profile.save()

        finance_profile.send_not_verified_email()
        finance_profile.refresh_from_db()
        send.assert_called()
        assert finance_profile.verified_email_sent is None
        assert finance_profile.not_verified_email_sent is not None
