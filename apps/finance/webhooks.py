"""
This module store webhook handlers via dj-stripe
For get registrations custom handlers, need to put them in a module is
imported like models.py


dj-stripe is responsible for updating data for customers, subscription,
plans, etc
"""
import logging

from django_fsm import TransitionNotAllowed
from djstripe import models, webhooks
from djstripe.event_handlers import _handle_crud_like_event
from djstripe.models import Event

from .models import (
    AccountProxy,
    PaymentIntentProxy,
    PlanProxy,
    SubscriptionProxy,
)
from .services import stripe_deposits_service

logger = logging.getLogger('stripe')


@webhooks.handler("invoice.payment_succeeded")
def handle_subscription_payment_succeeded(event: Event):
    """Handler provide actions for a successful complete or renewing
    subscription.

    * Renew the user's has_active_subscription
    * Check setting `featured` value for Attorney
    * Check setting `promo period` for first subscription

    Raise:
        DefinitionPlanTypeError if get error receiving the plan type

    """
    logger.info(event.data)

    user = event.customer.subscriber
    invoice, _ = _handle_crud_like_event(
        target_cls=models.Invoice,
        event=event,
    )
    subscription = SubscriptionProxy.objects.get(id=invoice.subscription.id)
    user.active_subscription = subscription
    user.save()
    # Get invoice object for to getting a related plan
    is_premium = PlanProxy.check_is_premium(invoice.plan)
    if is_premium:
        user.attorney.featured = True
        user.attorney.save()


@webhooks.handler(
    "invoice.payment_action_required",
    "invoice.payment_failed",
    "customer.subscription.deleted"
)
def handle_subscription_payment_failed(event: Event):
    """Handles cases where a attorney is denied access

    This happens if:
     * Payment failed
     * The subscription was canceled and ended

    Deactivate Attorney access to paid resources,
    disable `featured` capabilities

    """
    logger.info(event.data)

    user = event.customer.subscriber
    if event.type == "customer.subscription.deleted":
        subscription_id = event.data['object']['id']
    else:
        invoice, _ = _handle_crud_like_event(
            target_cls=models.Invoice,
            event=event,
        )
        subscription_id = SubscriptionProxy.objects.get(
            id=invoice.subscription.id
        ).id

    # do nothing if user doesn't exist in DB anymore
    if not user:
        return

    # Event `"customer.subscription.deleted"` triggered for trial future
    # subscriptions. If this cancelled subcription isn't current for user
    # - nothing to do
    if (user.active_subscription and
            user.active_subscription.id == subscription_id):
        user.active_subscription = None
        user.save()
    if not user.active_subscription:
        user.attorney.featured = False
        user.attorney.save()


@webhooks.handler("invoice.created")
def handle_adding_promo_period_to_subscription(event: Event):
    """Handler provide promo period for emulation first 18-moth subscription

    Adding a promotional period is implement for "invoice.created" event,
    become invoice is created is created one hour before the charge is
    debited on the day the subscription ends

    Related docs:
    https://stripe.com/docs/billing/lifecycle#subscription-lifecycle

    TODO: this method should be removed after expiring subscriptions v1

    """
    logger.info(event.data)

    user = event.customer.subscriber
    invoice, _ = _handle_crud_like_event(
        target_cls=models.Invoice,
        event=event,
    )

    billing_reason = event.data['object']['billing_reason']

    # When the first year of subscription ends, set the trial within six months
    if all([
        not user.finance_profile.was_promo_period_provided,
        billing_reason == 'subscription_cycle']
    ):
        SubscriptionProxy.set_promo_period_v1(invoice.subscription)
        user.finance_profile.was_promo_period_provided = True
        user.finance_profile.save()


@webhooks.handler("account.updated")
def handle_account_updates(event: Event):
    """Handler to make some actions on Account update.

    Account info may be updated by stripe depending on its verification status
    (is it passed verification and ready for charges and payouts or not).

    Whenever new webhook come, method updates corresponding Account info in
    DB and sends emails about successful verification or not.

    """
    logger.info(event.data)
    account_id = event.data['object']['id']
    finance_profile = stripe_deposits_service.get_finance_profile(account_id)
    if not finance_profile:
        return

    # save account and send email to user about its status
    account, _ = _handle_crud_like_event(target_cls=AccountProxy, event=event)
    account.notify_user()


@webhooks.handler("capability.updated")
def handle_capability_updates(event: Event):
    """Handler to update Account `capabilities` on its update.

    Capabilities changes are tracked separately with `capabilities` stripe API,
    cause we can't get this info with just `Account` resync (it is not actual
    there). There is a problem that stripe sends no `final` event that
    `account.updated` after pending `individual.id_number` verification
    succeeds. So we can know that verification is completed at the end just
    from the `capability.updated` event. But when we get `capability.updated`
    event we can't just resync Account data and get updated info, because
    Account would be moved from `pending` to `completed` state only after few
    minutes from the last `capability.updated` `active` event.

    """
    logger.info(event.data)
    account_id = event.data['object']['account']
    finance_profile = stripe_deposits_service.get_finance_profile(account_id)
    if not finance_profile:
        return

    # refresh account info just in case if it was updated
    account = AccountProxy.resync(account_id)
    stripe_deposits_service.update_capability(
        account, event.data['object']['id']
    )
    account.refresh_from_db()
    account.notify_user()


@webhooks.handler(
    "account.external_account.created",
    "account.external_account.deleted",
    "account.external_account.updated",
)
def handle_external_account_updates(event: Event):
    """Handler to make some actions on External Account update.

    External Account info may be updated by user in his Express account
    dashboard. Whenever new webhooks come, method updates corresponding
    Account Info in DB.

    """
    logger.info(event.data)
    account_id = event.data['object']['account']
    finance_profile = stripe_deposits_service.get_finance_profile(account_id)
    if not finance_profile:
        return

    # refresh account `external_accounts` and notify user about his status
    account = AccountProxy.resync(account_id)
    account.notify_user()


@webhooks.handler(
    'payment_intent.succeeded',
    'payment_intent.canceled',
    'payment_intent.payment_failed',
)
def payment_intent_status_change(event: Event):
    """Handle successful failed or canceled invoice payment

    Related docs:
    https://stripe.com/docs/payments/intents

    """
    logger.info(event.data)

    payment_intent, _ = _handle_crud_like_event(
        target_cls=PaymentIntentProxy,
        event=event,
    )
    # Payment intent is not attached to payment, skipping
    if not payment_intent.payment:
        return

    transition_map = {
        'payment_intent.succeeded': 'finalize_payment',
        'payment_intent.canceled': 'cancel_payment',
        'payment_intent.payment_failed': 'fail_payment',
    }

    payment = payment_intent.payment
    try:
        getattr(payment, transition_map[event.type])()
        payment.save()
    except TransitionNotAllowed:
        pass
