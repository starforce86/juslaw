import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from djstripe.enums import SubscriptionStatus
from stripe.error import InvalidRequestError, StripeError

from libs.utils import invalidate_cached_property

from apps.finance import factories, models
from apps.finance.exceptions import PaymentProfileCreationError

pytestmark = pytest.mark.django_db


class TestProductProxyModel:
    """Tests for `ProductProxy` model methods."""

    def test_get_or_create_existing(
        self, product: models.ProductProxy, mocker
    ):
        """Check `get_or_create` method works correctly.

        Check that when Product with the same `id` already exists - it will
        be returned.

        """
        create = mocker.patch('apps.finance.models.ProductProxy.create')
        result_product, is_created = models.ProductProxy.get_or_create(
            id=product.id
        )
        assert result_product == product
        assert not is_created
        create.assert_not_called()

    def test_get_or_create_not_existing(self, mocker):
        """Check `get_or_create` method works correctly.

        Check that when Product with the `id` doesn't exist - it will
        be created and returned.

        """
        create = mocker.patch(
            'apps.finance.models.ProductProxy.create',
            return_value=models.ProductProxy()
        )
        result_product, is_created = models.ProductProxy.get_or_create(
            id=str(uuid.uuid4())
        )
        assert result_product == create.return_value
        assert is_created
        create.assert_called()

    def test_create(self, mocker):
        """Check `create` method works correctly.

        Check that on new ProductProxy creation there are made required stripe
        API calls through SDK.

        """
        data = {'id': str(uuid.uuid4())}

        api_create = mocker.patch(
            'apps.finance.models.ProductProxy._api_create',
            return_value=data
        )
        sync_from_stripe = mocker.patch(
            'apps.finance.models.ProductProxy'
            '.sync_from_stripe_data',
            return_value=data
        )

        result = models.ProductProxy.create(**data)
        api_create.assert_called_with(**data)
        sync_from_stripe.assert_called_with(data)
        assert result == data


class TestPlanProxyModel:
    """Tests for `PlanProxy` model methods."""

    def test_get_or_create_existing(self, plan: models.PlanProxy, mocker):
        """Check `get_or_create` method works correctly.

        Check that when Plan with the same `id` already exists - it will
        be returned.

        """
        create = mocker.patch(
            'apps.finance.models.PlanProxy.create'
        )
        result, is_created = models.PlanProxy.get_or_create(id=plan.id)
        assert result == plan
        assert not is_created
        create.assert_not_called()

    def test_get_or_create_not_existing(self, mocker):
        """Check `get_or_create` method works correctly.

        Check that when Plan with the `id` doesn't exist - it will
        be created and returned.

        """
        create = mocker.patch(
            'apps.finance.models.PlanProxy.create',
            return_value=models.PlanProxy()
        )
        result, is_created = models.PlanProxy.get_or_create(
            id=str(uuid.uuid4())
        )
        assert result == create.return_value
        assert is_created
        create.assert_called()

    def test_purge_existing(self, plan: models.PlanProxy, mocker):
        """Check `purge` method works correctly.

        Check that when Plan exists in both `stripe` and `backend` - it will
        be removed everywhere.

        """
        api_delete = mocker.patch(
            'apps.finance.models.PlanProxy._api_delete',
            return_value=None
        )
        model_delete = mocker.patch('djstripe.models.Plan.delete')

        plan.purge()
        # check that all required methods were called
        api_delete.assert_called()
        model_delete.assert_called()

    def test_purge_no_such_plan_exception(
        self, plan: models.PlanProxy, mocker
    ):
        """Check `purge` method works correctly.

        Check that when Plan exists only in `backend` - it will be removed
        from DB even though there is `stripe` `No such plan` API error.

        """
        plan.delete()
        api_delete = mocker.patch(
            'apps.finance.models.PlanProxy._api_delete',
            side_effect=InvalidRequestError(
                message='No such plan:', param=None
            )
        )
        model_delete = mocker.patch('djstripe.models.Plan.delete')

        plan.purge()
        # check that all required methods were called
        api_delete.assert_called()
        model_delete.assert_called()

    def test_purge_another_exception(self, plan: models.PlanProxy, mocker):
        """Check `purge` method works correctly.

        Check that when Plan exists only in `backend` - it won't be removed
        from DB if there is `stripe` not `No such plan` API error and exception
        will be raised.

        """
        mocker.patch(
            'apps.finance.models.PlanProxy._api_delete',
            side_effect=InvalidRequestError(
                message='Another error:', param=None
            )
        )

        with (pytest.raises(InvalidRequestError)):
            plan.purge()

    def test_delete(self, plan: models.PlanProxy, mocker):
        """Check `delete` method works correctly.

        Check that when Plan is deleted via `delete` method - there is called
        a `purge` method inside.

        """
        purge = mocker.patch('apps.finance.models.PlanProxy.purge')
        plan.delete()
        purge.assert_called()

    def test_create(self, mocker):
        """Check `create` method works correctly."""
        data = {
            'id': str(uuid.uuid4()),
            'description': 'test',
            'livemode': True,
            'nickname': 'fake',
            'empty': ''
        }
        create = mocker.patch(
            'djstripe.models.Plan.create',
            return_value=factories.PlanProxyFactory(
                id=data['id'], nickname=data['nickname']
            )
        )
        # create new plan
        result = models.PlanProxy.create(**data)
        # check results
        create.assert_called_with(id=data['id'], nickname=data['nickname'])
        assert result.id == data['id']
        assert result.description == data['description']
        assert result.livemode
        assert result.name == result.nickname == data['nickname']
        assert not hasattr(result, 'empty')


class TestSubscriptionProxyModel:
    """Tests for `SubscriptionProxy` model methods."""

    def test_create(
        self, subscription: models.SubscriptionProxy, mocker
    ):
        """Check `create` method works correctly.

        Check that when new Subscription creation is successful - no errors
        are raised and `sync_from_stripe_data` was called.

        """
        create = mocker.patch(
            'stripe.Subscription.create', return_value=subscription
        )
        sync_from_stripe_data = mocker.patch(
            'apps.finance.models.SubscriptionProxy.sync_from_stripe_data'
        )
        create_args = {
            'customer_id': subscription.customer.id,
            'plan_id': str(subscription.plan_id),
            'trial_end': int(datetime.now().timestamp()),
        }
        models.SubscriptionProxy.create(**create_args)
        create.assert_called_once_with(
            customer=create_args['customer_id'],
            items=[{"plan": create_args['plan_id']}],
            off_session=True,
            trial_end=create_args['trial_end'],
        )
        sync_from_stripe_data.assert_called_once_with(subscription)

    def test_create_stripe_error(
        self, subscription: models.SubscriptionProxy, mocker
    ):
        """Check `create` method works correctly.

        Check that when new Subscription creation is not successful - errors
        are raised and no `sync_from_stripe_data` was called.

        """
        mocker.patch('stripe.Subscription.create', side_effect=StripeError())
        sync_from_stripe_data = mocker.patch(
            'apps.finance.models.SubscriptionProxy.sync_from_stripe_data',
        )
        create_args = {
            'customer_id': subscription.customer.id,
            'plan_id': str(subscription.plan_id),
            'trial_end': int(datetime.now().timestamp()),
        }
        with (pytest.raises(PaymentProfileCreationError)):
            models.SubscriptionProxy.create(**create_args)
            sync_from_stripe_data.assert_not_called()

    def test_fill_items_for_switch_plan(
        self, subscription: models.SubscriptionProxy, mocker
    ):
        """Check `fill_items_for_switch_plan` method works correctly."""
        fake_subscription = {
            'items': {
                'data': [MagicMock(id='1')]
            }
        }
        api_retrieve = mocker.patch(
            'apps.finance.models.SubscriptionProxy.api_retrieve',
            return_value=fake_subscription
        )
        result = subscription.fill_items_for_switch_plan('test')
        expected = [{'id': '1', 'plan': 'test'}]
        assert result == expected
        api_retrieve.assert_called_once()

    def test_switching_plan_immediately_active_subscription(
        self, subscription: models.SubscriptionProxy, mocker
    ):
        """Check `switching_plan_immediately` method works correctly."""
        subscription.status = SubscriptionStatus.active
        fake_fill_items = [{'id': '1', 'plan': 'test'}]
        mocker.patch(
            'apps.finance.models.SubscriptionProxy.fill_items_for_switch_plan',
            return_value=fake_fill_items
        )
        fake_subscription = MagicMock(id='subscription_1')
        modify = mocker.patch(
            'stripe.Subscription.modify', return_value=fake_subscription
        )
        create_invoice = mocker.patch('stripe.Invoice.create')
        sync_from_stripe = mocker.patch(
            'apps.finance.models.SubscriptionProxy'
            '.sync_from_stripe_data',
            return_value=fake_subscription
        )

        result = subscription.switching_plan_immediately('test')
        assert result == fake_subscription
        modify.assert_called_once_with(
            subscription.id,
            items=fake_fill_items,
            cancel_at_period_end=False
        )
        create_invoice.assert_called_once_with(
            customer=subscription.customer.id,
            auto_advance=True,
            subscription=fake_subscription.id,
            description=(
                f'Upgrade subscription {subscription.id} to plan test for '
                f'{subscription.customer}'
            ),
            default_payment_method=subscription.customer.
            default_payment_method.id
        )
        sync_from_stripe.assert_called_once_with(fake_subscription)

    def test_switching_plan_immediately_trialing_subscription(
        self, subscription: models.SubscriptionProxy, mocker
    ):
        """Check `switching_plan_immediately` method works correctly."""
        subscription.status = SubscriptionStatus.trialing
        fake_fill_items = [{'id': '1', 'plan': 'test'}]
        mocker.patch(
            'apps.finance.models.SubscriptionProxy.fill_items_for_switch_plan',
            return_value=fake_fill_items
        )
        fake_subscription = MagicMock(id='subscription_1')
        modify = mocker.patch(
            'stripe.Subscription.modify', return_value=fake_subscription
        )
        create_invoice = mocker.patch('stripe.Invoice.create')
        sync_from_stripe = mocker.patch(
            'apps.finance.models.SubscriptionProxy'
            '.sync_from_stripe_data',
            return_value=fake_subscription
        )

        result = subscription.switching_plan_immediately('test')
        assert result == fake_subscription
        modify.assert_called_once_with(
            subscription.id,
            items=fake_fill_items,
            cancel_at_period_end=False
        )
        create_invoice.assert_not_called()
        sync_from_stripe.assert_called_once_with(fake_subscription)

    def test_calculate_proration_cost(
        self, subscription: models.SubscriptionProxy, mocker
    ):
        """Check `calculate_proration_cost` method works correctly."""
        fake_fill_items = [{'id': '1', 'plan': 'test'}]
        fill_items = mocker.patch(
            'apps.finance.models.SubscriptionProxy.fill_items_for_switch_plan',
            return_value=fake_fill_items
        )
        upcoming = mocker.patch(
            'stripe.Invoice.upcoming',
            return_value=MagicMock(lines=MagicMock(data=[]))
        )
        cost, _ = subscription.calculate_proration_cost('test')
        assert cost == 0
        fill_items.assert_called_once_with('test')
        upcoming.assert_called_once()

    def test_calculate_proration_cost_error(
        self, subscription: models.SubscriptionProxy, mocker
    ):
        """Check `calculate_proration_cost` method works correctly."""
        mocker.patch(
            'apps.finance.models.SubscriptionProxy.fill_items_for_switch_plan',
            side_effect=StripeError()
        )
        with (pytest.raises(StripeError)):
            subscription.calculate_proration_cost('test')


class TestCustomerProxyModel:
    """Tests for `CustomerProxy` model methods."""

    def test_create_with_payment_data_existing(
        self, customer, mocker,
    ):
        """Check `create_with_payment_data` method works correctly.

        Check that when payment plan is set for existing customer, everything
        works ok and corresponding stripe API method is called.

        """
        create = mocker.patch(
            'apps.finance.models.CustomerProxy.get_or_create',
            return_value=(customer, False)
        )
        add_payment_method = mocker.patch(
            'apps.finance.models.CustomerProxy.add_payment_method'
        )
        payment_method = 'pm_123'
        result = models.CustomerProxy.create_with_payment_data(
            customer.subscriber, payment_method
        )
        assert result == customer
        create.assert_called_once_with(subscriber=customer.subscriber)
        add_payment_method.assert_called_once_with(payment_method)

    def test_create_with_payment_data_new(
        self, customer, mocker,
    ):
        """Check `create_with_payment_data` method works correctly.

        Check that when payment plan is set for new customer, everything
        works ok and corresponding stripe API method is called and new customer
        is created.

        """
        fake_customer = models.CustomerProxy(subscriber=customer.subscriber)
        create = mocker.patch(
            'apps.finance.models.CustomerProxy.get_or_create',
            return_value=(fake_customer, True)
        )
        add_payment_method = mocker.patch(
            'apps.finance.models.CustomerProxy.add_payment_method'
        )
        payment_method = 'pm_123'
        result = models.CustomerProxy.create_with_payment_data(
            customer.subscriber, payment_method
        )
        assert result == fake_customer
        create.assert_called_once_with(subscriber=customer.subscriber)
        add_payment_method.assert_called_once_with(payment_method)

    def test_create_with_payment_data_stripe_error(
        self, customer, mocker,
    ):
        """Check `create_with_payment_data` method works correctly.

        Check that when payment plan is set for a user and there is a stripe
        error -> there should be raised a `PaymentProfileCreationError` error.

        """
        mocker.patch(
            'apps.finance.models.CustomerProxy.get_or_create',
            side_effect=StripeError()
        )
        add_payment_method = mocker.patch(
            'apps.finance.models.CustomerProxy.add_payment_method'
        )
        with (pytest.raises(PaymentProfileCreationError)):
            models.CustomerProxy.create_with_payment_data(
                customer.subscriber, 'pm_123'
            )
            add_payment_method.assert_not_called()

    def test_current_subscription(
        self, customer,
        subscription: models.SubscriptionProxy
    ):
        """Check `current_subscription` method works correctly."""
        assert customer.current_subscription is not None
        customer.subscriber.active_subscription = None
        customer.subscriber.save()

        # invalidate cache for `cached_property` to get new results
        # now after first `customer` instance call there is a cached
        # `active_subscription` with a None value
        invalidate_cached_property(customer, 'current_subscription')
        assert customer.current_subscription is None

    def test_next_subscription(
        self, customer,
        subscription: models.SubscriptionProxy,
        another_subscription: models.SubscriptionProxy,
    ):
        """Check `next_subscription` method works correctly."""
        # as far as `subscription` is not trialing
        customer.subscriptions.all().delete()
        assert customer.next_subscription is None

        # add trialing subscription and check results after invalidation
        trialing_subscription = factories.SubscriptionProxyFactory(
            customer=customer,
            status=SubscriptionStatus.trialing
        )
        another_subscription.status = SubscriptionStatus.trialing
        another_subscription.save()

        # invalidate cache for `cached_property` to get new results
        # now after first `customer` instance call there is a cached
        # `active_subscription` with a None value
        invalidate_cached_property(customer, 'next_subscription')
        assert customer.next_subscription == trialing_subscription
