# Stripe integration in JLP project

## Subscriptions

Project has few different types of subscriptions `v1` and `v2`:

    - `v1` - subscriptions created in a 1st app version, which have separate
    logic of `promo` period handling (old one).
    
    - `v2` - subscriptions from a 2d app version, which have new and current
    logic of `promo` period handling.

### Subscriptions v1

**Business logic:** client should get money for subscription before trial period
will be finished.

**Implementation:**

For first subscription we emulate 18 month period. Stripe does not 
support long period (more than a year)

1. Create a subscription for the attorney
2. Get first successful payment invoice 
3. When the first year of subscription ends, we set the promo within six 
months (via the mechanism of the trial period in stripe). These implement in
webhook `handle_adding_promo_period_to_subscription`
4. Therefore, payment for the new next period is postponed for six months (we 
get those same 18 months)
5. At the end of the set promotional period - the customer is paying for the 
next year

### Subscriptions v2

**Business logic:** client manually provides ``trial_end`` for each attorney
on its `verification` process.

**Implementation:**

Such kind of subscriptions will always have ``was_promo_period_provided`` flag
enabled in corresponding user's FinanceProfile. So,
`handle_adding_promo_period_to_subscription` webhook wouldn't add extra trial
as for subscriptions on `v1`.
 
#### Feature:

When calculating the switching to premium, the user subscription usage time
will be counted. For example, a user changes a premium subscription after
six months of using a standard subscription. Since half the time was not used
in the first period, the difference cost will return to customer balance. 

It’s normal for current case that half the cost is returned, and not one third
of the 18 month subscription. 


## Direct deposits

By `direct deposits` naming means workflow of client direct payment for
attorney's invoice from the app or support user pays some fee to app to become
a support. 

For performing Direct Deposits feature there is used `Stripe connect` service.
As far as used on backend `dj-stripe` package doesn't support `Connect`
features (it just stores some Connect models in DB), there are added some
custom models with extra info and existing in `djstripe` models proxies to add
required connect behavior.

Useful links:

- used in JLP app account type - https://stripe.com/docs/connect/express-accounts
- validation - https://stripe.com/docs/connect/identity-verification, https://stripe.com/docs/connect/identity-verification-api
- capabilities - https://stripe.com/docs/connect/account-capabilities - JLP uses
`transfers`, `card payments` and `U.S. tax reporting` ones.
- form customization - https://dashboard.stripe.com/account/branding, https://dashboard.stripe.com/account/applications/settings
- charges and fees - https://stripe.com/docs/connect/charges, https://stripe.com/docs/connect/destination-charges
- payouts - https://stripe.com/docs/connect/bank-debit-card-payouts, https://stripe.com/docs/api/external_accounts
- pricing - https://stripe.com/connect/pricing
- test data - https://stripe.com/docs/connect/testing

### Invoice payments

#### Creation of attorney's connected account

If attorney wants to receive invoices payments within the JLP app, he should
create a new stripe connected ``express account`` to which client would send
his money. In JLP app ``attorney`` may create his express account only once.

Steps to create and fill out attorney's connected account:

- GET ``/finance/deposits/auth/url/`` - api method to get connected `express`
account authorization url. When user tries to call this method for a first time,
when he has no ``connected account`` yet - he would successfully get auth link.
Next time when user will try to get `authorization link` he would get 403
permissions error that he is not able to call this method again.

After getting an ``express account authorization url`` user should go for this
link and start registration of a new `connected` account with actual or test
data when registration proceeds user will be redirected to ``success_url`` from
request params. In case of some errors - he would be redirected to ``error_url``.

- GET ``/finance/deposits/profiles/current/`` - api method to get current user
`express` account info, it is updated via stripe connect `webhook`, so when
stripe needs more info or sets some info to a bad one - user info in this method
would be updated. The most important param is ``is_verified`` which designates
whether current user account is verified and he can start getting payments for
invoices to it.

When stripe updates user info via `webhook`, there can be sent `email`
notification to user when:

- some extra data needs to be added or there was added incorrect data on
account registration and it should be updated. In this case only 1 email
notification would be sent per day. So when user added wrong information for
a second time - he would get no notification about it. Notification contains
link to update current user's profile info.

- user account successfully verified 
 
- GET ``/finance/deposits/profiles/current/login-url/`` - api method to get a
link to current attorney user connected account, so he could add some extra
info or change payment method - from `bank account` to `credit card` and vice
versa (https://stripe.com/docs/connect/express-dashboard).

When user account `is_verified` becomes `True` - it means that user can get
invoices payments now. All payments firstly go to its connected account and then
once a day they are sent to his `bank account` or `credit card`
(https://stripe.com/docs/connect/bank-debit-card-payouts).

#### Pay for invoice

To start paying for invoice there should be used following methods:

- GET `/finance/payments/start/` - api method to initiate payment for some
object (invoice or support), it checks whether desired object is in appropriate
state (may user pay for it or not) and then returns new `Payment` object with
its `current` payment status if there are no errors.

Invoice can be paid only if:
    - its related attorney has verified ``connected express account``
    (`deposit_account`)
    - it has not 0 fees
    - its invoice in ``sent`` `status` and haven't been `paid` yet
    (`payment_status` in `not_started`, `in_progress`, `failed`)

- POST `/finance/payments/{id}/cancel/` - user may cancel payment if it is in
allowed for canceling payment state.

Invoice payment can be canceled if:
    - its ``payment_status`` is `in_progress` or `failed`

### Support payments

Support payments are implemented in a similar to ``invoices payments`` way, but
with the only difference that there are omitted steps of ``connected express
account`` creation (cause money would always go to JLP stripe account).

So it has the same api methods as in ``Pay for invoice`` section.

Support can pay only if:
    - its ``payment_status`` is not `paid` yet
    (`payment_status` in `not_started`, `in_progress`, `failed`)
    - support is verified by admin
    
Support payment can be canceled if:
    - its ``payment_status`` is `in_progress` or `failed`

### Payments refunds

JLP admin can refund any desired `payments` from attorney back to client by
visiting admin at `/admin/finance/paymentintentproxy/`. 

There he should open needed `PaymentIntent` and then click on
`VIEW ON STRIPE DASHBOARD` button. After stripe dashboard will be opened with
all information about payment, including `refund` option.
Also you can get to payment intent at `/admin/finance/payment/` admin.


### Pricing

- It's ok that JLP platform should pay each month for each `active` connected
account (account which had payouts to bank account or credit card this month). 
They just need to figure out what amount they should add to `app fee` to cover
this (it shouldn't be a percent, cause for low payments it wouldn't cover the
expense, but for big ones it would take too much).

- It's ok that JLP platform pays for `0.25% + 0.25 cents of payout`. Its logic
is similar to paying for products in a store. When people buy smth in
supermarkets they don't pay separately to a bank for ``paying by card``, these
expenses takes `seller` if he wants to provide a convinient feature of
`paying by card` to customers. He just increases his products price on some
percent according to this expense. 
So the same with JLP, there should be just increased `app fee` to cover this. 
