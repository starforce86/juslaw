from django.urls import reverse_lazy
from django.utils import timezone

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import FORBIDDEN, OK

from apps.finance import factories


def get_cancel_subscription_url():
    """Get url for `cancel_subscription`."""
    return reverse_lazy('v1:attorney-subscription-cancel-subscription')


def get_reactivate_subscription_url():
    """Get url for `reactivate_subscription`."""
    return reverse_lazy('v1:attorney-subscription-reactivate-subscription')


def get_preview_change_subscription_url():
    """Get url for `preview_change_subscription`."""
    return reverse_lazy('v1:attorney-subscription-preview-change-subscription')


def get_change_subscription_url():
    """Get url for `change_subscription`."""
    return reverse_lazy('v1:attorney-subscription-change-subscription')


class TestClientUserAPI:
    """Test `SubscriptionOptions` api for client users.

    Clients can't have access to this API.

    """

    @pytest.mark.parametrize(
        argnames='url,',
        argvalues=(
            get_cancel_subscription_url,
            get_reactivate_subscription_url,
            get_preview_change_subscription_url,
            get_change_subscription_url
        ),
    )
    def test_subscription_options_access(
        self, auth_client_api: APIClient, url
    ):
        """Test access to SubscriptionOptions."""
        response = auth_client_api.post(url())
        assert response.status_code == FORBIDDEN


class TestAttorneyUserAPI:
    """Test `SubscriptionOptions` api for attorney users.

    Attorneys have access to this API.

    """

    def test_cancel_subscription(
        self, api_client: APIClient, mocker, subscription,
        finance_profile
    ):
        """Test `cancel_subscription` method works correctly."""
        cancel_current_subscription = mocker.patch(
            'apps.finance.services.subscriptions.StripeSubscriptionsService'
            '.cancel_current_subscription',
            return_value=subscription,
        )
        url = get_cancel_subscription_url()
        api_client.force_authenticate(user=finance_profile.user)
        response = api_client.post(url)
        assert response.status_code == OK
        assert response.data['id'] == subscription.id
        cancel_current_subscription.assert_called_once()

    def test_reactivate_subscription(
        self, api_client: APIClient, mocker, subscription,
        finance_profile
    ):
        """Test `reactivate_subscription` method works correctly."""
        reactivate_cancelled_subscription = mocker.patch(
            'apps.finance.services.subscriptions.StripeSubscriptionsService'
            '.reactivate_cancelled_subscription',
            return_value=subscription,
        )
        url = get_reactivate_subscription_url()
        api_client.force_authenticate(user=finance_profile.user)
        response = api_client.post(url)
        assert response.status_code == OK
        assert response.data['id'] == subscription.id
        reactivate_cancelled_subscription.assert_called_once()

    def test_preview_change_subscription(
        self, api_client: APIClient, mocker, subscription,
        finance_profile
    ):
        """Test `preview_change_subscription` method works correctly."""
        plan = factories.PlanProxyFactory()
        expected_data = {
            'new_renewal_date': timezone.now(),
            'cost': 100
        }
        calc_subscription_changing_cost = mocker.patch(
            'apps.finance.services.subscriptions.StripeSubscriptionsService'
            '.calc_subscription_changing_cost',
            return_value=expected_data
        )
        url = get_preview_change_subscription_url()
        api_client.force_authenticate(user=finance_profile.user)
        response = api_client.post(url, data={'plan': plan.id})
        assert response.status_code == OK
        assert response.data == {
            'new_renewal_date': timezone.now().strftime('%Y-%m-%d'),
            'cost': '100.00'
        }
        calc_subscription_changing_cost.assert_called_once_with(new_plan=plan)

    def test_change_subscription(
        self, api_client: APIClient, mocker, subscription,
        finance_profile
    ):
        """Test `change_subscription` method works correctly."""
        plan = factories.PlanProxyFactory()
        change_subscription_plan = mocker.patch(
            'apps.finance.services.subscriptions.StripeSubscriptionsService'
            '.change_subscription_plan',
            return_value=subscription
        )
        url = get_change_subscription_url()
        api_client.force_authenticate(user=finance_profile.user)
        response = api_client.post(url, data={'plan': plan.id})
        assert response.status_code == OK
        assert response.data['id'] == subscription.id
        change_subscription_plan.assert_called_once_with(new_plan=plan)
