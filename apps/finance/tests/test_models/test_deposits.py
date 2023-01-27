import json

from django.conf import settings

import pytest
from djstripe import settings as djsettings

from apps.finance import models

from ...constants import Capabilities
from ...factories import AccountProxyFactory

pytestmark = pytest.mark.django_db


class TestWebhookEventTriggerProxyModel:
    """Tests for `WebhookEventTriggerProxy` model methods."""

    @pytest.mark.parametrize(
        argnames='body, webhook_secret',
        argvalues=(
            (
                str(json.dumps(dict(
                    id="1", livemode=False, api_version="2019-10-08", data={}
                ))),
                settings.DJSTRIPE_WEBHOOK_SECRET
            ),
            (
                str(json.dumps(dict(
                    id="1", livemode=False, account="123",
                    api_version="2019-10-08", data={}
                ))),
                settings.DJSTRIPE_CONNECT_WEBHOOK_SECRET
            )
        )
    )
    def test_validate_event(self, mocker, body, webhook_secret):
        """Check `validate` uses correct webhook secret key."""
        verify_header = mocker.patch(
            'stripe.WebhookSignature.verify_header',
            return_value=True
        )
        event = models.WebhookEventTriggerProxy.objects.create(
            body=body,
            headers={},
            remote_ip='127.0.0.1'
        )
        is_valid = event.validate()
        assert is_valid
        verify_header.assert_called_with(
            body,
            None,
            webhook_secret,
            djsettings.WEBHOOK_TOLERANCE
        )


class TestAccountProxyModel:
    """Tests for `AccountProxy` model methods."""

    @pytest.mark.parametrize(
        argnames='charges_enabled, payouts_enabled, requirements, '
                 'has_info, capabilities, expected_is_verified',
        argvalues=(
            # not valid: `charges` and `payouts`
            (False, False, {'eventually_due': []}, False, {}, False),
            # not valid: `charges`
            (False, True, {'eventually_due': []}, False, {}, False),
            # not valid: `payouts`
            (True, False, {'eventually_due': []}, False, {}, False),
            # not valid: `eventually_due`
            (True, True, {'eventually_due': ['passport']}, False, {}, False),
            # not valid: `has_info` and `capabilities`
            (
                True, True, {'eventually_due': []}, False,
                {c: 'pending' for c in Capabilities.default}, False
            ),
            # not valid: `has_info`
            (True, True, {'eventually_due': []}, False, {}, False),
            # not valid: `capabilities`
            (
                True, True, {'eventually_due': []}, True,
                {c: 'pending' for c in Capabilities.default}, False
            ),
            # all valid
            (
                True, True, {'eventually_due': []}, True,
                {c: 'active' for c in Capabilities.default}, True
            ),
        )
    )
    def test_is_verified(
        self, charges_enabled: bool, payouts_enabled: bool,
        requirements: dict, has_info: bool, capabilities: dict,
        expected_is_verified: bool
    ):
        """Test behavior of `is_verified` property."""
        account = AccountProxyFactory(
            charges_enabled=charges_enabled,
            payouts_enabled=payouts_enabled,
            requirements=requirements,
        )
        if has_info:
            info, _ = models.AccountProxyInfo.objects.get_or_create(
                account=account
            )
            info.capabilities = capabilities
            info.save()

        is_verified = account.is_verified
        assert is_verified == expected_is_verified

    @pytest.mark.parametrize(
        argnames='requirements, expected',
        argvalues=(
            ({'eventually_due': []}, False),
            ({'eventually_due': ['passport']}, True),
        )
    )
    def test_has_issues(self, requirements: dict, expected: bool):
        """Test behavior of `has_issues` property."""
        account = AccountProxyFactory(
            charges_enabled=False,
            payouts_enabled=False,
            requirements=requirements,
        )
        assert account.has_issues == expected

    @pytest.mark.parametrize(
        argnames='has_info',
        argvalues=(False, True)
    )
    def test_sync_from_stripe_data(self, mocker, has_info):
        """Check that `sync_from_stripe_data` method works correctly."""
        account = AccountProxyFactory()
        if has_info:
            old_info = models.AccountProxyInfo.objects.create(account=account)
            account.refresh_from_db()

        assert has_info == hasattr(account, 'info')

        mocker.patch(
            'djstripe.models.Account.sync_from_stripe_data',
            return_value=account
        )
        data = {'capabilities': {'1': 1}, 'external_accounts': {'2': 2}}
        models.AccountProxy.sync_from_stripe_data(data)

        # check that `capabilities` and `external_accounts` info is saved
        account.refresh_from_db()
        assert account.info.external_accounts == data['external_accounts']
        if has_info:
            assert old_info.id == account.info.id
            # when info already existed no `capabilities` update should be made
            assert account.info.capabilities == {}
        else:
            assert account.info.capabilities == data['capabilities']


class TestAccountProxyInfoModel:
    """Tests for `AccountProxyInfo` model methods."""

    not_all_active_capabilities = {
        Capabilities.CAPABILITY_TRANSFERS: 'active',
        Capabilities.CAPABILITY_TAX_REPORTING_US_1099_K: 'pending',
        Capabilities.CAPABILITY_TAX_REPORTING_US_1099_MISC: 'active',
        Capabilities.CAPABILITY_CARD_PAYMENTS: 'pending',
    }

    @pytest.mark.parametrize(
        argnames='capabilities, is_valid',
        argvalues=(
            ({}, False),
            ({c: '' for c in Capabilities.default}, False),
            ({'test': 'test'}, False),
            (not_all_active_capabilities, False),
            ({c: 'active' for c in Capabilities.default}, True),
        )
    )
    def test_validate_capabilities(self, capabilities, is_valid):
        """Check `validate_capabilities` method works correctly."""
        account = AccountProxyFactory()
        info = models.AccountProxyInfo.objects.create(
            account=account, capabilities=capabilities
        )
        assert info.validate_capabilities() == is_valid
