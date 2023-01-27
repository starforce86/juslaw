# Changelog for Django backend v2

### 2.0.44

Restrict VoiceConsents API. Now:

     - GET `/business/voice-consent/`, `/business/voice-consent/{id}/` -
     available for clients, attorneys, shared attorneys and support

     - POST `/business/voice-consent/` - available for clients only

     - DELETE `/business/voice-consent/{id}/` - available for  clients,
     attorneys, shared attorneys and support

There is no `PUT` and `PATCH` methods available anymore.

Task: [JLP-919](https://saritasa.atlassian.net/browse/JLP-919)

### 2.0.43

Rename `Support` to `Paralegal` in Django Admin and email and push
notifications. Also renamed `SUPPORT_USER_FEE` to `PARALEGAL_USER_FEE`.

Task: [JLP-912](https://saritasa.atlassian.net/browse/JLP-912)

### 2.0.42

**Set up health check api**

Available checks:
* `cache`
* `email`
* `database`
* `firestore`
* `stripe`
* `rabbitMQ`
* `s3_storage`
* `redis`
* `celery`

Health check api url: GET `/api/v1/utils/health-check/`

Health check page: `/health-check/`

Task: [JLP-884](https://saritasa.atlassian.net/browse/JLP-884)


### 2.0.41

Add possibility to edit network for all network participants:
`PUT, PATCH /social/group-chats/{id}/`

Task: [JLP-879](https://saritasa.atlassian.net/browse/JLP-879)


### 2.0.40

**Improve transition error feedback**

Now it's possible to raise `ValidationError` in model's status
transition permission check to show why user can't do it.

Task: [JLP-771](https://saritasa.atlassian.net/browse/JLP-771)


### 2.0.39

**Add `created_by` to Invoice**

Task: [JLP-860](https://saritasa.atlassian.net/browse/JLP-860)


### 2.0.38

**Admin app improvements**

* `Business`
  * `Checklist Entries` - Forbid to edit attorney of a checklist, 
    add attorney autocomplete_fields to speed up admin
  * `Invoice` - Forbid to edit matter
  * `Leads` - Update list view and move topic after priority, detail view - 
    forbid to change client, attorney, topic, status after creation
  * `Matters` - Update list view and move lead field after title, detail view - 
    forbid to change client, attorney, lead after creation.
  * `Notes` - Forbid to change matter, created_by after creation + 
    add matter and created_by fields to autocomplete_fields
  * `Stages` - Add attorney to autocomplete_fields, make attorney field readonly after creation
  * `BillingItem` - Forbid to change matter after creation
  * `VoiceConsent` - Forbid to change matter after creation

* `Cities light`
  * Make all `cities_light` admins readonly

* `Finance`
  * Forbid to add new plans and product proxies
  * Move `DjStripe` admin into finance section

* `Forums`
  * `Categories` - Forbid to change related specialty
  * `Posts` - Forbid to change topic and author after creation
  * `Topics` - Forbid to change topic's category

* `Celery beat`
  * Make all `celery_beat` admins readonly
 
* `Promotion`
  * `Events` - Forbid to change attorney after create

* `Social`
  * `Group chat` - Forbid to change creator after group chat creation
  * `Post` - Forbid to change creator after post creation

* `Users`
  * `Users` `Attorney`, `Client`, `Support` - Forbid to change user after creation, 
    add links to profiles
  * `Invites` - Forbid to change inviter after create

* `FCM django`
  * Made panel read only

* `Removed panels`: `Token`, `Email addresses`, `Tag`(from `taggit`) and `Group`

Task: [JLP-847](https://saritasa.atlassian.net/browse/JLP-847)

### 2.0.37

**Add `title` to voice consent**

Task: [JLP-854](https://saritasa.atlassian.net/browse/JLP-854)


### 2.0.36

**Set up read only api for `MatterSharedWith` model.**

Task: [JLP-848](https://saritasa.atlassian.net/browse/JLP-848)


### 2.0.35

Fix notification that Matter `status` updated.

Task: [JLP-843](https://saritasa.atlassian.net/browse/JLP-843)


### 2.0.34

**Set up Fee Payments for Support(Staff) users**

Same as with invoices payments:
POST `api/v1/finance/payments/start/` - Get payment for object and 
set it's status to `Payment in progress`. For example to get payment for support user, 
you need to send this:
```json
{
   "object_type": "support",
   "object_id": 1
}
```

Task: [JLP-819](https://saritasa.atlassian.net/browse/JLP-819)


### 2.0.33

**Add `New Matter Shared` notification**

Available for `Attorneys` and `Supports`

Task: [JLP-813](https://saritasa.atlassian.net/browse/JLP-813)


### 2.0.32

Add new type of users ``Support`` with its own `user` API and possibility to 
work on shared with them matters and its related stuff (similar to
`share matter` business logic).

1. There were added following ``Support`` users API endpoints:

    - GET `/users/support/` - get all system support users, returns `verified`
    and `paid` platform fee support profiles (payment logic would be
    implemented later).

    - POST `/users/support/` - registration for a new `Support` users, it works
    similar to attorneys registration - user registered, then platform admin
    should ``verify`` it from Django Admin. When user becomes `verified` or
    `declined` he gets email notification about his current status. After
    successful verification ``Support`` user should pay `platform fee` and after
    that he would be available in `support` users list and can work on `shared`
    with him matters.

    - GET `/users/support/{user}/` - get detail info about any `support` user.

    - GET `/users/support/current/` - get current `support` user profile info.

    - PUT, PATCH `/users/support/current/` - update current `Support` user
    profile info.
    
2. Extend GET `/users/` with `support` boolean filter, which filters `verified`
support users.

3. Extend POST `/business/matters/{id}/share/` with `user_type` field
(`support` or `attorney`), it allows to update matter's `share_with` with
either `attorneys` or `support` users (by default if no `user_type` is set
method works with `attorney`). When method works with one user type, it ignores
input data for another user types and does nothing with another user type in
matter's `shared_with` field.

4. Extend `business` app API, so `shared` support users may work with it.
Shared support users have almost the same permissions as shared attorneys,
except new matters creation:

    - `matters` - read, update, change status, close matter
    - `latest_activity` - read
    - `stage` - read matters stages
    - `checklist entries` - read matters checklist entries
    - `matter topic` - create, read
    - `matter post` - create, read
    - `video call` - create with shared matter `client`
    - `notes` - CRUD for own notes for shared matter only
    - `resources` - read
    - `folders` - CRUD for shared matter folders
    - `documents` - CRUD for shared matter documents
    - `invoices` - CRUD for shared matter
    - `time billing` - CRUD for shared matter

Task: [JLP-818](https://saritasa.atlassian.net/browse/JLP-818)

### 2.0.31

**Set up endpoints and webhooks for direct invoice payments**

* POST `api/v1/finance/payments/start/` - Get payment for object and 
 set it's status to `Payment in progress`. For example to get payment for invoice, you need to send this
 ```json
 {
    "object_type": "invoice",
    "object_id": 1
 }
 ```
* POST `api/v1/finance/payments/{id}/cancel/` - Cancel payment
* Add webhook processing for stripe events(`payment_intent.succeeded`, `payment_intent.canceled`, 
 `payment_intent.payment_failed`). Also set up email notifications for user.
* Update admin panel for `Invoice` model
* Set up `Payment` model to track payment toward any model.
* Add admin panel for `PaymentIntentProxy` model and `Payment` model.

Task: [JLP-770](https://saritasa.atlassian.net/browse/JLP-770)


### 2.0.30

**Prepare backend for Invoice payments**

* Add new invoice statuses -> `Paid` and `Payment in prosess`. Paid or in process of payment invoice and same with 
 time billings can not be edited.
* Refactor invoice status transitions. Make them like matters
* Update `BillingItemAttachment` related signal to support new pay logic
* Add `service` to prepare invoice for payment
* Refactor business signals

Explanation of invoices statuses:
* `Pending` -> Set when invoice `is created`. Can't be seen by client.
* `Sent` -> Set when invoice `is sent` to client or when `payment is canceled`.
* `Payment in progress` -> Set when client starting paying for invoice
 (when `front-end requests payment_intent`).
* `Payment failed` -> Set when client's payment failed, but client can try again.
* `Paid` -> Set payment for invoice was successful.

Statuses when attorney `can edit` invoice and related to it time billings -> `Pending` or `Sent`
Statuses when attorney `can't edit` invoice and related to it time billings -> `Payment in progress` or `Paid`
You can find out whenever you `can edit or not` by checking out `available_for_editing` field

Task: [JLP-768](https://saritasa.atlassian.net/browse/JLP-768)


### 2.0.29

**Now all new users will have enabled notifications by default**

Task: [JLP-809](https://saritasa.atlassian.net/browse/JLP-809)


### 2.0.28

**Add workflow for Stripe Direct Deposits**

1. Add new API methods to provide possibility to create new Express accounts
from stripe:

    -  GET ``/finance/deposits/auth/url/`` - returns Stripe Express Account
    authorization url to which user should be redirected to start attaching his
    direct deposits account. This method is available only for `verified`
    attorneys, which have no connected account for direct deposits yet.
    
    - GET ``/finance/deposits/auth/callback/`` - stripe connect oAuth callback
    triggered on new Express account creation automatically. It gets taken from
    ``/finance/deposits/auth/url/`` url `success_url` and `error_url` and
    depending on result status makes user redirect. So if user is redirected
    to ``success_url`` his account successfully created, otherwise - there are
    some issues and user should try account creation one more time.

2. Add API methods to get user's deposit account details and link to its stripe
dashboard:
    
    - GET `/finance/deposits/profiles/current/` - get info about user's
    connected account for stripe direct deposits with required for frontend
    info:
        - `is_verified` (designate whether user is verified by stripe or
        should fill or update his info). Account considered as verified if:
        `charges_enabled=True`, `payouts_enabled=True`,
        `requirements['eventually_due]` field is empty, `pending_verification`
        field is empty and all default `capabilities` are active (`transfers`, 
        `card_payments`, `tax_reporting_us_1099_k`,
        `tax_reporting_us_1099_misc`) 

        - `bank_external_account` (attached bank info for payouts)

        - `card_external_account` (attached card info for payouts)
    
    Returned `AccountProxy` data would contain only one of
    `bank_external_account` or `card_external_account` fields, so another one
    would be `null` (because Express account allows to attach only one of them)
    
    - GET `/finance/deposits/profiles/current/login-url/` - get link to user's
    connected Express account dashboard, where he can add or update his info.

3. Also there is added fix for stripe ``webhook`` processing endpoint
(overridden ProcessWebhookView to use custom WebhookEventTriggerProxy model).
It was needed because of `djstripe` (it has almost no support for stripe
connect). So there was no possibility to define separate `webhook secret` for
stripe connect webhook validation (`verify_signature`).

4. Update management command ``create_webhook``, now it creates a simple
`subscriptions` webhook (`account` type) and `direct deposits` webhook
(`connect` type) depending on defined `--type` argument.

5. Add few models in DB for nice support of Stripe connect - 
WebhookEventTriggerProxy, AccountProxy, AccountProxyInfo and extend
FinanceProfile model with new fields `deposit_account`,
`not_verified_email_sent`, `verified_email_sent`, which store required direct
deposit `account` info for user.

6. Added few webhooks methods, which control updates on ``account`` and its
`external_accounts` info and there is following logic:

    - when ``account.updated`` event comes - app updates related AccountProxy
    instance in DB and checks whether it is verified by stripe or not and
    sends email notifications if it is needed:
    
        - account not verified - if user had no `email` that his account is
        not verified at all or for the last day - he would get an `account not
        verified` notification with a link to user's stripe account dashboard,
        so he could add or update information. In other words, user should get
        `account not verified` notification only once a day (cause there can
        be too many webhook calls from stripe for the day). Also whenever any
        ``account not verified`` notification is sent - there is remembered
        sent datetime in `not_verified_email_sent` field of user's
        FinanceProfile and `verified_email_sent` field is reset (sets to None).
        
        - account is verified - if user had no `email` that his account is
        verified at all - he would get ``account verified`` notification. This
        notification won't be sent again until user's account becomes
        ``not verified`` and then `verified` again. Whenever any
        ``account verified`` notification is sent - there is remembered
        sent datetime in `erified_email_sent` field of user's FinanceProfile
        and `not_verified_email_sent` field is reset (sets to None).
    
    - when any of `account.external_account.created`,
    `account.external_account.deleted`, `account.external_account.updated`
    events comes - app updates related AccountProxy
    instance in DB and remembers a new account info in `external_accounts`

Task: [JLP-767](https://saritasa.atlassian.net/browse/JLP-767)


### 2.0.27

Improve invoices export to QuickBooks. Added ``BillEmail`` to invoice, which is
the same as `Customer` primary email address. Also improved error message on
``duplicated`` client name.

Task: [JLP-715](https://saritasa.atlassian.net/browse/JLP-715)


### 2.0.26

**Add `sponsor_link` to Attorney model**

Task: [JLP-810](https://saritasa.atlassian.net/browse/JLP-810)


### 2.0.25

**Fix issues that were found in sentry**

* Fix `IntegrityError` on `DocuSign` profile retrieval 
 Issue: [JLP-40](https://sentry.saritasa.io/saritasa/jlp/issues/4160/)
* Fix `FCMDevice.MultipleObjectsReturned` in `FCM` api `get_object`
 Issue: [JLP-2D](https://sentry.saritasa.io/saritasa/jlp/issues/3957/)
* Fix false positive issue(sentry reported `logger.error`, when exception was expected) for `DocuSign` in `sentry` 
 Issue: [JLP-2X](https://sentry.saritasa.io/saritasa/jlp/issues/4070/)
* Fix false positive issue(sentry reported `logger.error`, when exception was expected) for `DocuSign` API in `sentry`
 Issue: [JLP-1W](https://sentry.saritasa.io/saritasa/jlp/issues/3783/)
* Fix false positive issue(sentry reported `logger.error`, when exception was expected) for `DocuSign` on `jwt_token` retrieval 
 Issue: [JLP-22](https://sentry.saritasa.io/saritasa/jlp/issues/3795/)
* Move `django_cities_light` update task to `12pm` 
 Issue: [JLP-31](https://sentry.saritasa.io/saritasa/jlp/issues/4075/)
* Also: 
  * Add active filter for `Stripe` Customer Admin

Task: [JLP-746](https://saritasa.atlassian.net/browse/JLP-746)

### 2.0.24

**Add Network posts feature for attorneys**

* New endpoints at (`/api/v1/social/posts/`)

Task: [JLP-753](https://saritasa.atlassian.net/browse/JLP-753)

### 2.0.23

Add possibility to invite users from `share_matter`. Add `emails` field in
`/business/matters/{id}/share-matter/`. Whenever matter is shared with not
existing user through `emails` field there would be created new Invite instance
for a required email, inviter, matter, title and message and there would be
sent and invite to defined `email`.

When new user is registered with which some matter was shared - he should be
automatically added to `shared_with` Matter users and he should get a
`matter shared` notification when he would be `verified` by admin.

Task: [JLP-757](https://saritasa.atlassian.net/browse/JLP-757)

### 2.0.22

1. Extend backend with possibility and permissions to `share` matter with
another users. Added `MatterSharedWith` model and Django Admin for it, API
method to control users with which matter is shared:

- POST `/business/matters/{id}/share/` - it allows to share matter with
defined `participants` (provides remove and add new participants functionality),
also when matter is shared with a new user there is sent an email
notification. For now this method allows to select only `attorneys` users.
Matters in `draft` or `pending` statuses can't be shared. Also it's not
allowed to update Matter's `esign_documents` list by shared users (it is
available for matter owner only).

2. To `Matter` API entity there are added `shared_with`,
`shared_with_data` and `is_shared` readonly fields, which help to designate
with which users matter is shared.

3. Extend `stage` and `checklist` api with `matter` query param (filter),
so when it is set - there will be returned not request user attorney entities,
but entities related to shared matter attorney. Attorney with which matter was
shared has only READ permission for `stage` and `checklist` API. When
`matter` query param is not set - there will be return own user entities.

    - GET `/business/stages/?matter=1`
    - GET `/business/checklist/?matter=1`

4. There were updated some filters for `clients`:

  - GET `/users/clients/?has_matter_with_user=True` - returns also clients from
  shared matters
  - GET `/users/clients/?user_clients=True` - returns also clients from
  shared matters


5. There is added a separate API method to get users with which matter
can be shared:

    - GET `/users/` with available filtration by `attorneys` (only attorneys
    users), `clients` (only clients users), `available_for_share_matter`
    (available for sharing in matter users).


6. Updated `latest activity` generation, now for Matter `status` changes there
would be generated a title with `shared` user name (if it was done by shared
user) or original attorney name (if it was done by matter's attorneys). The
same logic is added to `send invoice` API action (`/business/invoices/1/send`).
For MatterPost, Note, Document and matter creation - everything should work by
user initiated action too.

7. Now to attorney's matter statistics there are also added `shared` matters
info at the same time with `owned` matter info.

So far now, when `matter` is shared with some user, this `user` should have
the same permissions for matter and its related APIs:
    - `matters` - CRUD, change status, close matter
    - `latest_activity` - read
    - `stage` - read matters stages, CRUD for own ones
    - `checklist entries` - read matters checklist entries, CRUD for own ones
    - `matter topic` - create, read
    - `matter post` - create, read
    - `video call` - create with shared matter `client`
    - `notes` - CRUD for own notes for shared matter only
    - `resources` - read
    - `folders` - CRUD for shared matter folders
    - `documents` - CRUD for shared matter documents
    - `invoices` - CRUD for shared matter
    - `time billing` - CRUD for shared matter

Task: [JLP-756](https://saritasa.atlassian.net/browse/JLP-756)

### 2.0.21

**Add new notification type `New Network`**

This notification is sent when attorney is invited to `group chat`.

Task: [JLP-759](https://saritasa.atlassian.net/browse/JLP-759)

### 2.0.20

**Add endpoint to leave group_chat**

* New endpoint (`/api/v1/social/group-chats/{id}/leave/`)

Task: [JLP-749](https://saritasa.atlassian.net/browse/JLP-749)

### 2.0.19

**Add social app**

* Add new model GroupChat(works same as `Chat` model)
* Add api for social app's group chats (`/api/v1/social/group-chats`)

Task: [JLP-748](https://saritasa.atlassian.net/browse/JLP-748)

### 2.0.18

**Migrate from `centos7` to `python:3.8.2-slim-buster`**

Move to `python:3.8.2-slim-buster`, because it easier and faster to change `python` versions
and it has `gdal` version(`2.4`) supported by `Django 3`.

Task: [JLP-386](https://saritasa.atlassian.net/browse/JLP-386)

### 2.0.17

**Minor improvements**

* Add auto complete filter for admin
* Refactor business app models placement
* Fix up queries for AP
* Correct search fields in admin

Task: [JLP-386](https://saritasa.atlassian.net/browse/JLP-386)

### 2.0.16

**Migrate to Django 3 and Python 3.8**

* Update `django` to `3.0.6`
* Update `python` to `3.8.2`
* Update `django-cacheops` to `5.0`
* Update `django-allauth` to `0.0.42`
* Update `django-taggit` to `1.3.0`
* Update `djangorestframework` to `3.11.0`
* Update `dj-stripe` to `2.3.0`
* Update `redis` to `3.5.2`
* Update `docusign_esign` to `3.2.0`
* Update `django-cors-headers` to `3.3.0`
* Update `Dockerfile` to support Django 3
* Fix production settings file
* Fix usage of `ugettext_lazy` to `gettext_lazy`
* Improve `pre-commit` and `pre-push`
* Add clean commands for docker and improve docker provision

Task: [JLP-386](https://saritasa.atlassian.net/browse/JLP-386)

### 2.0.15

Add `remove` action in Django admin to make deletion with ignorance of
`PROTECT` flags. Also added new provision script to fill local DB
`data.fill-sample-data`. 

Task: [JLP-386](https://saritasa.atlassian.net/browse/JLP-386)

### 2.0.14

Add API methods for Invoice export in QuickBooks:

- GET `/api/v1/accounting/export/customers/` - get all available for user
customers from his QuickBooks account;

- POST `/api/v1/accounting/export/invoice/` - start invoice export to user's
QuickBooks account.

All these endpoints are available for only authenticated in QuickBooks users.

Task: [JLP-723](https://saritasa.atlassian.net/browse/JLP-723)

### 2.0.13

Prepare backend for Invoices creation and back sync - added separate QBInvoice
model, which stores info about already exported invoices; added backend methods
for further invoice exporting.

Task: [JLP-722](https://saritasa.atlassian.net/browse/JLP-722)

### 2.0.12

Add new `accounting` app responsible for QuickBooks attorney integration. Also
added authorization workflow API for QuickBooks:

- GET `/api/v1/accounting/auth/url/` - get QB authorization url, available to
`active` attorneys only;

- GET `/api/v1/accounting/auth/callback/` - special method for QB, which is
triggered by QB on attorney approve/decline app access request, after
successful or not successful getting of `authorization tokens` redirects user
to defined in `/api/v1/accounting/auth/url/` `success_url` or `error_url`. If
requested `state` doesn't exist - redirects user to dashboard.

Task: [JLP-715](https://saritasa.atlassian.net/browse/JLP-715)

### 2.0.11

***Prepare for group chat feature***

* Add `chats` app with chat model
* Rework interactions with `firestore`
    * Remove `first_name_another_participant` and `last_name_another_participant`
    * Replace `another_participant_id` with array `participants_ids`
* Fix resync with `firestore`
* Update `firestore-admin` package 

Task: [JLP-720](https://saritasa.atlassian.net/browse/JLP-720)

### 2.0.10

***Add feature to download app stats as excel file in admin***

Task: [JLP-708](https://saritasa.atlassian.net/browse/JLP-708)


### 2.0.9

**Add feature for attorneys to download business stats**

New endpoint: 
 * GET `/api/v1/business/statistics/export`

Task: [JLP-709](https://saritasa.atlassian.net/browse/JLP-709)

### 2.0.8

**Refactoring of version 2.0**

* Remove social accounts from admin
* Remove pages app
* Remove unused docs files
* Update sphinx compose config
* Improve version display
* Make notification app admin read only
* Migrate to pipenv

Task: [JLP-386](https://saritasa.atlassian.net/browse/JLP-386)


### 2.0.7

***Make notifications for new posts in followed topics available for attorneys***

Refactor folder structure for notification resources

Task: [JLP-690](https://saritasa.atlassian.net/browse/JLP-690)


### 2.0.6

***Update admin***

Update `admin` to use our custom admin site and add `dashboard panel` with app `statistics`(
just amounts of certain things like `attorneys` or `matters`)

Task: [JLP-671](https://saritasa.atlassian.net/browse/JLP-671)


### 2.0.5

***Add video call feature***

Clients and attorneys can now create video calls in `jitsi`, all video call participants will be notified by push or 
email(depending on settings)

Video call endpoint:
* `/api/v1/business/video-calls/`

Task: [JLP-635](https://saritasa.atlassian.net/browse/JLP-635)


### 2.0.4

***Add news pages feature***

* Add news model and it's `tags` models `NewsTag` and `NewsCategory`
* Add admin panel and `django-taggit-labels` for better UX
* Add to ckeditor, a feature to upload images through `S3`
* Add api for new feature(views, serializers and filters)
* Add tests for new feature

New endpoints:
* `/api/v1/news/`
* `/api/v1/news/tags`
* `/api/v1/news/categories` 

Task: [JLP-636](https://saritasa.atlassian.net/browse/JLP-636)


### 2.0.3

***Add voice consent feature***

Client can now upload it's `voice consent` for matter. Client have full `CRUD` access, while
attorney can only view `voice consent`.

Voice consent endpoint:
* `/api/v1/business/voice-consent/` VoiceConsentViewSet

Task: [JLP-635](https://saritasa.atlassian.net/browse/JLP-635)


### 2.0.2

***Add `sponsored` field to attorney model***

If `attorney` is somehow `sponsored` `Jus-Law`, then `admin` sets this field
to true and this `attorney` will show up on special place on main page of site. 

(It's alternative to `featured` field)

Task: [JLP-632](https://saritasa.atlassian.net/browse/JLP-632)


### 2.0.1

***Add `templates` feature***

* Add `is_template` field to resource model
* Make `owner` field nullable
* Update `documents` and `folders` admin panels for easier integrations
* Bump `django-object-actions` to `2.0`

**Add tests for `templates` feature**

* Add tests related to templates feat for models
* Update querysets tests
* Extend api tests for document app
* Add signal tests for document app
* Add migration for main global template folder creation

Task: [JLP-605](https://saritasa.atlassian.net/browse/JLP-605)


### 2.0.0

Bump from `1.1.11`
