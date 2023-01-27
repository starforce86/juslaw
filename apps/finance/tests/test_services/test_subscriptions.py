from django.utils.timezone import now

import arrow
import pytest
from djstripe.enums import SubscriptionStatus

from libs.utils import invalidate_cached_property

from apps.finance import exceptions, factories, models
from apps.finance.constants import PlanTypes
from apps.finance.exceptions import InvalidSubscriptionAction
from apps.finance.factories import SubscriptionProxyFactory
from apps.finance.services.subscriptions import StripeSubscriptionsService
from apps.users.factories import AppUserFactory, AttorneyFactory
from apps.users.models import Attorney


@pytest.fixture(scope='module')
def another_attorney(django_db_blocker) -> Attorney:
    """Create another Attorney"""
    with django_db_blocker.unblock():
        return AttorneyFactory()


class TestStripeSubscriptionsService:
    """Base class for `StripeSubscriptionsService` related tests."""

    def test_verify_subscription_no_subscription(self, another_attorney):
        """Check that `verify_subscription` method works correctly.

        When user has no `active` subscription - there should be raised
        InvalidSubscriptionAction.

        """
        service = StripeSubscriptionsService(another_attorney.user)
        assert not service.subscription
        with pytest.raises(exceptions.InvalidSubscriptionAction):
            service.verify_subscription()

    def test_verify_subscription_not_valid(self, attorney):
        """Check that `verify_subscription` method works correctly.

        When user has `active` subscription, but it is not valid - there
        should be raised InvalidSubscriptionAction.

        """
        subscription = factories.SubscriptionProxyFactory(
            customer__subscriber=attorney.user
        )
        attorney.user.active_subscription = subscription
        attorney.user.save()
        service = StripeSubscriptionsService(attorney.user)
        assert service.subscription
        with pytest.raises(exceptions.InvalidSubscriptionAction):
            service.verify_subscription()

    def test_verify_subscription_canceled_not_valid(self, attorney):
        """Check that `verify_subscription` method works correctly.

        When we validate subscription for `cancelling` and user has `active`
        subscription, it is valid but is not canceled - there should be raised
        InvalidSubscriptionAction.

        """
        subscription = factories.SubscriptionProxyFactory(
            customer__subscriber=attorney.user,
            status=SubscriptionStatus.active,
            trial_end=arrow.now().shift(days=10).datetime
        )
        attorney.user.active_subscription = subscription
        attorney.user.save()
        service = StripeSubscriptionsService(attorney.user)
        assert service.subscription
        with pytest.raises(exceptions.InvalidSubscriptionAction):
            service.verify_subscription(is_canceled=True)

    def test_verify_subscription(self, attorney):
        """Check that `verify_subscription` method works correctly.

        When user has `active` subscription and it is valid - verification
        should pass.

        """
        subscription = factories.SubscriptionProxyFactory(
            customer__subscriber=attorney.user,
            status=SubscriptionStatus.active,
            trial_end=arrow.now().shift(days=10).datetime
        )
        attorney.user.active_subscription = subscription
        attorney.user.save()
        service = StripeSubscriptionsService(attorney.user)
        assert service.subscription
        service.verify_subscription()

    def test_create_initial_subscription_error(self, finance_profile, mocker):
        """Check that `create_initial_subscription` method works correctly.

        Check that when any error appears during new subscription creation
        there would be raised SubscriptionCreationError.

        """
        mocker.patch(
            'apps.finance.models.SubscriptionProxy.create',
            side_effect=ValueError()
        )
        assert finance_profile.user.customer
        assert not finance_profile.was_promo_period_provided

        with pytest.raises(exceptions.SubscriptionCreationError):
            trial_end = arrow.now().shift(days=10).date()
            StripeSubscriptionsService.create_initial_subscription(
                finance_profile.user, trial_end
            )
        assert not finance_profile.was_promo_period_provided

    def test_create_initial_subscription(self, finance_profile, mocker):
        """Check that `create_initial_subscription` method works correctly.

        Check that when new `initial` subscription is successfully created ->
        `was_promo_period_provided` would be updated.

        """
        create = mocker.patch('stripe.Subscription.create')
        mocker.patch(
            'apps.finance.models.SubscriptionProxy.sync_from_stripe_data',
        )
        assert finance_profile.user.customer
        assert not finance_profile.was_promo_period_provided

        trial_end = arrow.now().shift(days=10).date()
        StripeSubscriptionsService.create_initial_subscription(
            finance_profile.user, trial_end
        )
        assert finance_profile.was_promo_period_provided
        create.assert_called_once_with(
            customer=finance_profile.user.customer.id,
            items=[{"plan": finance_profile.initial_plan_id}],
            off_session=True,
            trial_end=int(arrow.get(trial_end).timestamp)
        )

    def test_cancel_current_subscription(self, customer, subscription, mocker):
        """Check that `cancel_current_subscription` method works correctly.

        Check that current user subscription is canceled with
        `at_period_end=True` and next one with `at_period_end=False`.

        """
        cancel_subscription = mocker.patch(
            'apps.finance.models.SubscriptionProxy.cancel'
        )
        next_subscription = mocker.patch(
            'apps.finance.models.CustomerProxy.next_subscription',
        )

        StripeSubscriptionsService(
            customer.subscriber
        ).cancel_current_subscription()
        # check that method was called twice with correct params
        cancel_subscription.assert_called_once_with(at_period_end=True)
        next_subscription.assert_has_calls([
            mocker.call.cancel_subscription(at_period_end=False)
        ])

    def test_calc_subscription_changing_cost_no_subscription(
        self, another_attorney, plan
    ):
        """Check that `calc_subscription_changing_cost` works correctly.

        Check that when there is no `active_subscription` for user there will
        be returned a full cost of a plan and `now` as a new renewal date.

        """
        user = another_attorney.user
        assert user.active_subscription is None
        result = StripeSubscriptionsService(
            user
        ).calc_subscription_changing_cost(plan)
        assert result['new_renewal_date'].date() == now().date()
        assert result['cost'] == (plan.amount / 100)

    def test_calc_subscription_changing_cost_wrong_subscription_status(
        self, plan
    ):
        """Check that `calc_subscription_changing_cost` works correctly.

        Check that method raises error if subscription has not `trialing` or
        `active` status.

        """
        user = AppUserFactory()
        user.active_subscription = SubscriptionProxyFactory(
            customer__subscriber=user,
            status=SubscriptionStatus.canceled
        )
        user.save()
        with pytest.raises(InvalidSubscriptionAction):
            StripeSubscriptionsService(user).calc_subscription_changing_cost(
                plan
            )

    def test_calc_subscription_changing_cost_trial_subscription(
        self, mocker, customer, subscription, plan
    ):
        """Check that `calc_subscription_changing_cost` works correctly.

        Check that for `trialing` subscription `calculate_proration_cost`
        method will be called for any new plan (standard/premium).

        """
        renewal_date = now()
        calculate_proration_cost = mocker.patch(
            'apps.finance.models.SubscriptionProxy.calculate_proration_cost',
            return_value=(100, renewal_date)
        )
        assert customer.subscriber.active_subscription == subscription
        assert subscription.is_trialing

        expected = {
            'new_renewal_date': renewal_date,
            'cost': 1
        }

        # check that `calculate_proration_cost` is called for trialing
        # subscription with not premium plan
        assert not models.PlanProxy.check_is_premium(plan)
        result = StripeSubscriptionsService(customer.subscriber) \
            .calc_subscription_changing_cost(plan)
        assert result == expected
        calculate_proration_cost.assert_called()

        # check that `calculate_proration_cost` is called for trialing
        # subscription with premium plan
        calculate_proration_cost.reset_mock()
        plan.metadata['type'] = PlanTypes.PREMIUM
        assert models.PlanProxy.check_is_premium(plan)
        result = StripeSubscriptionsService(customer.subscriber) \
            .calc_subscription_changing_cost(plan)
        assert result == expected
        calculate_proration_cost.assert_called()

    def test_calc_subscription_changing_cost_active_subscription_to_premium(
        self, mocker, customer, subscription, plan
    ):
        """Check that `calc_subscription_changing_cost` works correctly.

        Check that for `active` subscription `calculate_proration_cost`
        method will be called only for plan change to `premium`.

        """
        renewal_date = now()
        subscription.status = SubscriptionStatus.active

        calculate_proration_cost = mocker.patch(
            'apps.finance.models.SubscriptionProxy.calculate_proration_cost',
            return_value=(100, renewal_date)
        )
        assert customer.subscriber.active_subscription == subscription
        assert subscription.is_active

        expected = {
            'new_renewal_date': renewal_date,
            'cost': 1
        }

        # check that `calculate_proration_cost` is called for active
        # subscription with premium plan
        plan.metadata['type'] = PlanTypes.PREMIUM
        assert models.PlanProxy.check_is_premium(plan)
        result = StripeSubscriptionsService(customer.subscriber) \
            .calc_subscription_changing_cost(plan)
        assert result == expected
        calculate_proration_cost.assert_called()

    def test_calc_subscription_changing_cost_active_subscription_to_standard(
        self, mocker, customer, subscription, plan
    ):
        """Check that `calc_subscription_changing_cost` works correctly.

        For `standard` - there is just returned original subscription
        `renewal_date`.

        """
        subscription.status = SubscriptionStatus.active
        plan.metadata = {}
        calculate_proration_cost = mocker.patch(
            'apps.finance.models.SubscriptionProxy.calculate_proration_cost',
        )
        get_renewal_date = mocker.patch(
            'apps.finance.models.SubscriptionProxy.get_renewal_date',
            return_value=now()
        )
        assert customer.subscriber.active_subscription == subscription
        assert subscription.is_active
        assert not models.PlanProxy.check_is_premium(plan)

        # check that only `get_renewal_date` is called for active
        # subscription with not premium plan
        result = StripeSubscriptionsService(customer.subscriber) \
            .calc_subscription_changing_cost(plan)
        assert result == {'new_renewal_date': get_renewal_date.return_value}
        calculate_proration_cost.assert_not_called()
        get_renewal_date.assert_called()

    def test_change_subscription_plan_no_subscription(
        self, mocker, another_attorney, plan
    ):
        """Check that `change_subscription_plan` works correctly.

        Check that when there is no `active_subscription` for user there will
        be called a new subscription creation with a desired plan.

        """
        create = mocker.patch(
            'apps.finance.models.SubscriptionProxy.create',
            return_value=None
        )
        user = another_attorney.user
        assert user.active_subscription is None
        factories.CustomerProxyFactory(subscriber=user)
        invalidate_cached_property(user, 'customer')
        result = StripeSubscriptionsService(user).change_subscription_plan(
            plan
        )
        assert result is None
        create.assert_called_once()

    def test_change_subscription_plan_wrong_subscription_status(
        self, plan
    ):
        """Check that `change_subscription_plan` works correctly.

        Check that method raises error if subscription has not `trialing` or
        `active` status.

        """
        user = AppUserFactory()
        user.active_subscription = SubscriptionProxyFactory(
            customer__subscriber=user,
            status=SubscriptionStatus.canceled
        )
        user.save()
        with pytest.raises(InvalidSubscriptionAction):
            StripeSubscriptionsService(user).change_subscription_plan(plan)

    def test_change_subscription_plan_trial_subscription(
        self, mocker, customer, subscription, plan
    ):
        """Check that `change_subscription_plan` works correctly.

        Check that for `trialing` subscription `switching_plan_immediately`
        method will be called for any new plan (standard/premium).

        """
        subscription.status = SubscriptionStatus.trialing
        switching_plan_immediately = mocker.patch(
            'apps.finance.models.SubscriptionProxy.switching_plan_immediately',
            return_value=None
        )
        assert customer.subscriber.active_subscription == subscription
        assert subscription.is_trialing

        # check that `switching_plan_immediately` is called for trialing
        # subscription with not premium plan
        assert not models.PlanProxy.check_is_premium(plan)
        result = StripeSubscriptionsService(customer.subscriber) \
            .change_subscription_plan(plan)
        assert result is None
        switching_plan_immediately.assert_called()

        # check that `switching_plan_immediately` is called for trialing
        # subscription with premium plan
        switching_plan_immediately.reset_mock()
        plan.metadata['type'] = PlanTypes.PREMIUM
        assert models.PlanProxy.check_is_premium(plan)
        result = StripeSubscriptionsService(customer.subscriber) \
            .change_subscription_plan(plan)
        assert result is None
        switching_plan_immediately.assert_called()

    def test_change_subscription_plan_active_subscription_to_premium(
        self, mocker, customer, subscription, plan
    ):
        """Check that `change_subscription_plan` works correctly.

        Check that for `active` subscription `switching_plan_immediately`
        method will be called only for plan change to `premium`.

        """
        subscription.status = SubscriptionStatus.active
        switching_plan_immediately = mocker.patch(
            'apps.finance.models.SubscriptionProxy.switching_plan_immediately',
            return_value=None
        )
        assert customer.subscriber.active_subscription == subscription
        assert subscription.is_active

        # check that `switching_plan_immediately` is called for active
        # subscription with premium plan
        plan.metadata['type'] = PlanTypes.PREMIUM
        assert models.PlanProxy.check_is_premium(plan)
        result = StripeSubscriptionsService(customer.subscriber) \
            .change_subscription_plan(plan)
        assert result is None
        switching_plan_immediately.assert_called()

    def test_change_subscription_plan_active_subscription_to_standard(
        self, mocker, customer, subscription, plan
    ):
        """Check that `change_subscription_plan` works correctly.

        For `standard` - there will be called `switching_plan_at_end`.

        """
        subscription.status = SubscriptionStatus.active
        plan.metadata = {}
        switching_plan_immediately = mocker.patch(
            'apps.finance.models.SubscriptionProxy.switching_plan_immediately',
            return_value=None
        )
        switching_plan_at_end = mocker.patch(
            'apps.finance.models.SubscriptionProxy.switching_plan_at_end',
            return_value=None
        )
        assert customer.subscriber.active_subscription == subscription
        assert subscription.is_active
        assert not models.PlanProxy.check_is_premium(plan)

        # check that only `switching_plan_at_end` is called for active
        # subscription with not premium plan
        result = StripeSubscriptionsService(customer.subscriber)\
            .change_subscription_plan(plan)
        assert result is None
        switching_plan_immediately.assert_not_called()
        switching_plan_at_end.assert_called()
