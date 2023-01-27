# Changelog for Django backend v1

## Release 1.1

### 0.1.11

***Add fixes for `docusign` envelopes workflow***

Currently there is a problem in DocuSign that it removes all envelopes for
`demo` accounts after 30 days and only `draft` envelopes in production
after 30 days too without any notifications and webhooks.

https://support.docusign.com/articles/How-long-does-DocuSign-store-my-documents

To fix this problem there was added a `Clean old envelopes` celery task. It
would be run every day and it will try to remove old (older then 30 days)
envelopes from DB if they will be deleted in DocuSign. Task is run every day at
00:00 on server time.

Note: For ``production`` env there will be deleted only `created` envelopes.

Task: [JLP-674](https://saritasa.atlassian.net/browse/JLP-674)

### 1.1.10

***Add fixes for `trial` subscriptions workflow***

- Cancel - trial subscription can be canceled any time, but not `immediately`
(after period end - the same as active subscriptions)

- Reactivate - trial subscription can be reactivated any time with a previous
plan.

- Change preview - for trial subscriptions it will always return `0` cost.

- Change - for trial subscriptions we can change its plan anytime when it is
active and no upcoming invoices will be created.

Task: [JLP-645](https://saritasa.atlassian.net/browse/JLP-645)

### 1.1.9

***Add invoice filter by periods of time***

In this `filter`, we return invoices that have a least `one` day of it's period inside
input period. In other words we return invoices that:
* Have `period_start` and `period_end` between `input period start` 
* Have `period_start` and `period_end` between `input period end`
* Have `period_start` and `period_end` inside `input period start` and `end`
* Have `period_start` and `period_end` outside `input period start` and `end` 

Task: [JLP-601](https://saritasa.atlassian.net/browse/JLP-601)

### 1.1.8

Add possibility to edit ``trial_end`` date from Attorney Admin page. It is
available for already verified attorneys, who has ``trialing`` subscription
(shouldn't work for any other subscriptions statuses).

Task: [JLP-557](https://saritasa.atlassian.net/browse/JLP-557)

### 1.1.7

Update subscriptions functionality. Now on attorney verification process from
Django Admin there will be opened a window to select `trial end` date.

For old subscription behavior stays the same. Check out stripe docs:
https://jlp-backend.saritasa-hosting.com/docs/stripe.html


Task: [JLP-557](https://saritasa.atlassian.net/browse/JLP-557)

### 1.1.6

**Add email notification about registered client for inviter**

Task: [JLP-544](https://saritasa.atlassian.net/browse/JLP-544)

### 1.1.5

**Add display name property to user models**

In case of client, it either returns user's `full name` or `name of organization` 
(depends on client's type).

Task: [JLP-542](https://saritasa.atlassian.net/browse/JLP-542)

### 1.1.4

1. Added CRUD API for `invoices` - GET, POST, PUT, PATCH, DELETE
`/business/invoices/`, where POST, PUT, PATCH, DELETE is available for
attorneys only.

2. Added signals on Invoice creation or its ``periods`` update for `hourly`
rated matters:

    - Create - on invoice creation all matching BillingItems would be
    connected to it.

    - Update - on invoice `period` updates all new matching period time
    billings would be attached, matching old ones will stay the same and not
    matching anymore ones would be deleted.
    
    - Delete - on invoice deletion all related to it BillingItemAttachment
    links will be removed too.

3. Added signals on BillingItem creation or its ``date`` update for `hourly`
rated matters:
    
    - **create**
   
        * From Invoices: when TB is created from invoices page there will be
        always set ``invoice`` field in request data - API would perform
        validation of sent `invoice` and `date`. If validation is correct API
        will attach TB to all matching invoices. 
        
        * From Matters: when TB is created from matters page there will be
        absent `invoice` field in request data - API would automatically attach
        TB to matching invoices.
        
        To sum up, if `invoice` param is set - API would perform validation,
        otherwise API will try to automatically attach TB to matching invoices. 
        
    - **update**
    
    If Time Billing ``date`` field is changed - automatically reattach TB to
    matching invoices.

Rules of TB auto attaching to invoices:
   - all matching to date invoices links will stay
   - all not matching to date invoices links will be deleted
   - all new matching to date invoices links will be attached. 

Task: [JLP-514](https://saritasa.atlassian.net/browse/JLP-514)

### 1.1.3

**Add new fields for Client model and Invite model**

* `client_type` (`str`): Type of client(can be `Individual` or `Firm`)
* `organisation_name` (`str`): Name of client's organisation
* Add filters to `ClientViewSet` to get all invited clients and attorney
 clients

Task: [JLP-525](https://saritasa.atlassian.net/browse/JLP-525)

Task: [JLP-527](https://saritasa.atlassian.net/browse/JLP-527)

### 1.1.2

**Add feature for attorney to upload registration documents**

* Add the ability for an `attorney` who is registering to upload a `verification` 
 documents and edit them after verification
* Add the ability for an `admin` to download or upload these documents for `attorney` in 
 admin panel

Task: [JLP-511](https://saritasa.atlassian.net/browse/JLP-511)


### 1.1.1

**Improve feature to edit time billings.**

* Now on editing the correct invoice will be set or created.
* Add validation for time billing's date.

Task: [JLP-504](https://saritasa.atlassian.net/browse/JLP-504)


### 1.1.0

Bump from 1.0.139.

Task: [JLP-470](https://saritasa.atlassian.net/browse/JLP-470)

## Release 1.0

### 1.0.139

**Update notification email templates**

* Update email templates for notifications
* Add templates for emails subjects
* Add `deep links` to emails

Task: [JLP-501](https://saritasa.atlassian.net/browse/JLP-501)


### 1.0.138

**Update invoice formatting**

Task: [JLP-484](https://saritasa.atlassian.net/browse/JLP-484)


### 1.0.137

***Fix a link between `lead` and `matter`***

* Make relation between `lead` and `matter` as `one to many`
* Now on matter creation if matter has a lead it will marked as `completed` and added to
`converted lead` stats and won't be reused for `converted lead` stats

Task: [JLP-386](https://saritasa.atlassian.net/browse/JLP-386)


### 1.0.136

***Change attorney model***

* Remove `practice_jurisdictions_info` and `agency_info`

Task: [JLP-478](https://saritasa.atlassian.net/browse/JLP-478)


### 1.0.135

***Change attorney model***

* Add `agency_info` field(`required`) to `attorney`.
* Remove `matter_types` field.

Task: [JLP-467](https://saritasa.atlassian.net/browse/JLP-467)

Task: [JLP-468](https://saritasa.atlassian.net/browse/JLP-468)


### 1.0.134

***Change attorney model***

* Remove `bar_number` and `registration_number`.
* Add `license_info` and `practice_jurisdictions_info`. Both `required`.

Task: [JLP-456](https://saritasa.atlassian.net/browse/JLP-456)


### 1.0.133

***Remove attorney fields***

* Removed `fee_appropriate`

Task: [JLP-460](https://saritasa.atlassian.net/browse/JLP-460)


### 1.0.132

***Add `sentry` logging***

* Add `sentry` set up and logging
* Set up `sentry` report form for admin crashes

Task: [JLP-386](https://saritasa.atlassian.net/browse/JLP-386)


### 1.0.131

**Some minor improvements**

* Improve `new opportunities notification` email
* Make that email about attorney verification is sent when, verification status is being changed 
 by `verify_by_admin` or `decline_by_admin` methods
* Add `constance` fields for settings admins and maintainers emails
* Fix `time billing` fees calculation when time spent is 24h

Task: [JLP-386](https://saritasa.atlassian.net/browse/JLP-386)


### 1.0.130

***Change relation to `Client` model instead of `AppUser` for `Matter` and `Lead` models***

* Update tests and code
* Add `ProfileHelperMixin`, which contains common properties for `Attorney` and `Client` models

Task: [JLP-386](https://saritasa.atlassian.net/browse/JLP-386)

### 1.0.129

**Add `registration_number` to `Attorney` model**

Now `attorney` must have either `bar_number` or `registration_number` 

Task: [JLP-417](https://saritasa.atlassian.net/browse/JLP-417)


### 1.0.128

**Remove attorney fields**

Removed fields:
* `employment_year`
* `fee_last_average`
* `firm_name`
* `speciality_description`
* `speciality_significant_matter`

New field:
* `years_of_experience` - How long has attorney been practicing

Task: [JLP-423](https://saritasa.atlassian.net/browse/JLP-423)

Task: [JLP-424](https://saritasa.atlassian.net/browse/JLP-424)


### 1.0.127

***Move swagger `auto_schema` definitions to a separate file***

* Add `define_swagger_auto_schema` util, that used as shortcut for `swagger_auto_schema` decorator
* Add separate `schema.py` file with swagger spec for each app which was using `swagger_auto_schema`

Task: [JLP-386](https://saritasa.atlassian.net/browse/JLP-386)


### 1.0.126

**Add `Matter`'s statuses filter to `has_matter_with_user` filter for `ClientQuerySet`**

`has_matter_with_user` filter for `clients` now returns `clients` for attorney only with 
`active` or `completed` matters

Task: [JLP-404](https://saritasa.atlassian.net/browse/JLP-404)

### 1.0.125

Update generated on matters's status change `Activity` messages.

Task: [JLP-400](https://saritasa.atlassian.net/browse/JLP-400)

### 1.0.124

Restrict possibility to change ``url`` for FlatPages for not developers.

Task: [JLP-334](https://saritasa.atlassian.net/browse/JLP-334)

### 1.0.123

***Add tests for `users` app***

* Add tests for `models`
* Add tests for `querysets`
* Add tests for `signals`
* Fix `AdminsEmailNotification`'s recipient_list
* Add factory for generating `verified` and `not verified` attorney

Task: [JLP-289](https://saritasa.atlassian.net/browse/JLP-289)


### 1.0.122

***Add tests for `users` app api***

* Add tests for `registration`
* Add tests for `password reset`
* Add tests for `password change`
* Add tests for users `current profile` endpoints
* Add tests for `common users` endpoints
* Add tests for `follow attorney feature`
* Add tests for `invites api`
* Improve `pytest` configuration(add `plugin` to run tests in `parallel` and 
set paths to tests in `pytest.ini`)
* Update `pytest` and `pytest plugins`

Task: [JLP-289](https://saritasa.atlassian.net/browse/JLP-289)

### 1.0.121

Add tests for `esign` app. 

Task: [JLP-289](https://saritasa.atlassian.net/browse/JLP-289)

### 1.0.120

***Add tests for business api (part 2)***

* Add tests for `matters` api
* Add tests for `invoices` api
* Add tests for `matter topics` api
* Add tests for `matter posts` api
* Add tests for `activities` api
* Make `InvoicesViewSet` read only
* Remove `ability to delete` matters
* Make `send invoice` feature available only for `attorney`

Task: [JLP-289](https://saritasa.atlassian.net/browse/JLP-289)


### 1.0.119

Add new ``flat pages`` app and its Django Admin. It allows to add new simple
static pages in the app. In this admin it is allowed to update existing pages
only.

Also added autogenerated with migration ``about-us`` page, available by url:

    - GET `/pages/about-us/`

Task: [JLP-372](https://saritasa.atlassian.net/browse/JLP-372)


### 1.0.118

***Fix subscription workflow***

* Add delete next subscription, if attorney cancel current subscription
* Add "customer.subscription.deleted" event to `handle_subscription_payment_failed`

Task: [JLP-152](https://saritasa.atlassian.net/browse/JLP-152)


### 1.0.117

**Remove `followed` field from `TopicSerializer`**

Task: [JLP-217](https://saritasa.atlassian.net/browse/JLP-217)


### 1.0.116

***Remove redundant `address` fields form `Attorney` model***

Removed fields:
* `address_line_1`
* `address_line_2`
* `address_city`
* `address_state`
* `address_zip`

Now required fields:
* `firm_location`
* `firm_location_state`
* `firm_location_city`
* `firm_location_data`

Task: [JLP-375](https://saritasa.atlassian.net/browse/JLP-375)


### 1.0.115

***Add tests for business api***

* Improve `conftest` configuration for business app
* Add tests for `leads` api
* Add tests for `notes` api
* Add tests for `checklist` api
* Add tests for `stages` api
* Add tests for `time billing` api

Task: [JLP-289](https://saritasa.atlassian.net/browse/JLP-289)


### 1.0.114

***Add tests for `notifications app's api`***

* Add tests for `notification types` api
* Add tests for `notification settings` api
* Add `endpoints` to mark notification as `read` and `unread`(sent)
  * PATCH `/notifications/{id}/read/` to mark as `read`
  * PATCH `/notifications/{id}/unread/` to mark as `unread`(sent)
* Add tests for `notifications api`

Task: [JLP-289](https://saritasa.atlassian.net/browse/JLP-289)


### 1.0.113

Add possibility for client to create, update, delete matter's Notes from API:

    - POST `/api/v1/business/notes/`
    - PUT, DELETE `/api/v1/business/notes/{id}/`

Task: [JLP-368](https://saritasa.atlassian.net/browse/JLP-368)


### 1.0.112

***Add tests `notification` app***

* Add `tests` for `clean` and `save` logic for `notification models`
* Add tests for `querysets` for `notification models`
* Add tests for `notification resources`(for each `notification type`)
* Add tests for `NotificationDispatcher` 
* Add tests `signals` related to `notifications`

Task: [JLP-289](https://saritasa.atlassian.net/browse/JLP-289)


### 1.0.111

***Set up tests for promotion app***

* Add `db constraints` to `Event` model
* Add tests for `queryset`, `model restrictions`, `api`(`attorney` and `client` 
cases)

Task: [JLP-289](https://saritasa.atlassian.net/browse/JLP-289)


### 1.0.110

***Add tests for forums app***

* Add tests for `opportunities search`
* Add tests for `topics api`
* Add tests for `posts api`
* Add tests for `followed topic api`
* Fix permission for `opportunities` endpoint

Task: [JLP-289](https://saritasa.atlassian.net/browse/JLP-289)

### 1.0.109

Update latest activity message on Matter status change.

Task: [JLP-367](https://saritasa.atlassian.net/browse/JLP-367)


### 1.0.108

Improve Note API to return only notes `created_by` user:

- GET ``/api/v1/business/notes/``

Task: [JLP-368](https://saritasa.atlassian.net/browse/JLP-368)


### 1.0.107

***Improve admin panel for users app***

* Add `email` field to `attorney` and `client` `admin panels`
* Add `filtering` by `state` for `client admin panel`
* Make fields user and email clickable in `attorney` and `client` `admin panels`

Task: [JLP-354](https://saritasa.atlassian.net/browse/JLP-354)


### 1.0.106

**Add tests for duplicate feature in documents app**

Task: [JLP-289](https://saritasa.atlassian.net/browse/JLP-289)


### 1.0.105

1. Remove redundant POST `/business/matters/{id}/pending/` API method.

2. Updated behavior of ``activate`` API method. So when there is a try to
activate `revoked` matter:

* make it `active` if corresponding envelope has a `completed` status
    
* make it `draft` if corresponding envelope has `created` status
    
* make it `pending` if corresponding envelope has not `completed` and not 
`created` status
    
3. Make Matter `draft` again after reuploading esign documents (PUT 
`/business/matters/{id}/` with new `esign_documents`).

Task: [JLP-334](https://saritasa.atlassian.net/browse/JLP-334)


### 1.0.104

Add `sphinx-docs` for the project.

Task: [JLP-334](https://saritasa.atlassian.net/browse/JLP-334)


### 1.0.103

* Extend `SubscriptionOptions` with two endpoints:
    * POST `/api/v1/finance/subscription/change/preview/`
    * POST `/api/v1/finance/subscription/change/ `

* Change Subscription dates format to YYYY-MM-DD 
* Add methods for downgrade and upgrade subscriptions

 Task: [JLP-152](https://saritasa.atlassian.net/browse/JLP-152)


### 1.0.102

***Add tests for `documents` app***

* Add `db constraints` for `documents models`
* Add `tests` for `clean` and `save` logic for `documents models`
* Improve `querysets` for `documents models`
* Add test for `querysets` for documents models
* Add tests for `folders api`
* Add tests for `documents api`
* Forbid moving `resources` between `matters folders`(from one `matter`'s folder
to other `matter`'s folder)

Task: [JLP-289](https://saritasa.atlassian.net/browse/JLP-289)


### 1.0.101

***Add invite import***

* Add `invites` for `attorney` and `client` creation thought `import`
* Add `link setting` for attorney invite link
* Add extra fields to `Invite` model
* Update `django-import-export` to `2.0`

Task: [JLP-330](https://saritasa.atlassian.net/browse/JLP-330)


### 1.0.100

* Add `SubscriptionOptions` with two endpoints:
    * POST `/api/v1/finance/subscription/cancel/ `
    * POST `/api/v1/finance/subscription/reactivate/`

* Replace `has_active_subscription` to `active_subscription` (link to current `SubscriptionProxy` instance) In AppUser
* Refactor stripe helpers - add `StripeService` class 
* Updated `SubscriptionProxy` model: add methods for canceling and reactivating
* Update GET `/api/v1/finance/profiles/current/` - added `subscription_data`
* Update workflow webhooks
    * Delete adding promo period to start subscription 
    * Add store link to current subscription
* Change getting current subscription via adding `current_subscription` property to CustomerProxy
* Extend and update `SubscriptionSerializer`
* Add support old attorneys in IsAttorneyHasActiveSubscription

 Task: [JLP-152](https://saritasa.atlassian.net/browse/JLP-152)


### 1.0.99

***Set up clients notifications***

* Add new notification types `new_attorney_post`, `matter_status_update`, 
`document_shared_by_attorney`,`new_post` and set up `resources`, `signals` and `templates`
* Add `migration` to set all needed `types` and `groups`

Task: [JLP-320](https://saritasa.atlassian.net/browse/JLP-320)


### 1.0.98

***Set up attorneys notifications***

* Add new notification types `new_message`, `new_chat`, `new_opportunities` 
and set up `resources`, `signals` and `templates`
* Made `optimizations` to querysets in notifications api views
* Add `content` field for `NotificationSerializer`

Task: [JLP-320](https://saritasa.atlassian.net/browse/JLP-320)


### 1.0.97

Add API endpoint to validate Attorney registration steps:

  - POST `/api/v1/users/attorneys/validate-registration/`

API method accepts `stage` query parameter with available `first` and
`second` choices.

Task: [JLP-327](https://saritasa.atlassian.net/browse/JLP-327)


### 1.0.96

Add possibility to delete current user ESignProfile for Attorney:

- DELETE ``/api/v1/esign/profiles/current/``

Also add workaround for case when 2 attorneys use the same DocuSign account
(the company one) and one of them was fired - in such case we need to remove
ESignProfiles for all users with the same ``common`` DocuSign account and they
should perform consent obtaining again.

Task: [JLP-322](https://saritasa.atlassian.net/browse/JLP-322)


### 1.0.95

Add ``has_matter_with_user`` filter to Client API:

  - GET `/api/v1/users/clients/`

Task: [JLP-323](https://saritasa.atlassian.net/browse/JLP-323)


### 1.0.94

* Change initial subscription - added promo period (6 month) after first
 invoice
* Add validation for verify / decline attorney functionality 
* Add `was_promo_period_provided` to `FinanceProfile`
* Add `set_initial_promo_period` method in `SubscriptionProxy`
* Update `handle_subscription_payment_succeeded` webhook - add defining promo
 period datetime

Task: [JLP-261](https://saritasa.atlassian.net/browse/JLP-235)


### 1.0.93

***Update workflow for creation stripe plans and products***

* Update data for `./manage.py create_product_and_plans`
* Add `PlanProxy.purge` method
* Improved admins for plan \ products

Task: [JLP-299](https://saritasa.atlassian.net/browse/JLP-299)


### 1.0.92

Add Activities generation for matter:

1. When new matter is created -> `Matter created by {attorney}`
2. When matter status is updated -> `Matter status has been changed by {attorney}`
3. When invoice is sent -> `Invoice was sent to client by {attorney}`
4. When new note is created -> `Note has been added by {attorney}`
5. When new message is created -> `Message has been added by {author}`
6. When new document is added to shared folder -> `New file has been uploaded
to shared folder by {created_by}`

Task: [JLP-272](https://saritasa.atlassian.net/browse/JLP-272)

### 1.0.91

***Extend period statistics feature***
* Add model `UserStatistic`(to keep track over things)
* Add logic for stats generation (`active lead`, `active matters`, `converted
leads`)
* Add `celery` task that calculates every day `opportunities` for a day for
all `verified attorneys`
* Add helper `querysets` for `UserStatistic`
* Update `statistics collection services`
* Update `serializers` for `swagger` specs

Task: [JLP-278](https://saritasa.atlassian.net/browse/JLP-268)

### 1.0.90

**Make Events model save dates in naive time and api accept timezones for event dates**

Task: [JLP-286](https://saritasa.atlassian.net/browse/JLP-288)


### 1.0.89

***Update workflow for creation stripe plans and products***

* Update data for `./manage.py create_product_and_plans`
* Add `PlanProxy.purge` method
* Improved admins for plan \ products

Task: [JLP-299](https://saritasa.atlassian.net/browse/JLP-299)

### 1.0.88

***Implement push notifications***

* Set up `fcm_django` push notification workflow
* Add `html page with script` to `test` push notifications
* Update `settings templates`

Task: [JLP-172](https://saritasa.atlassian.net/browse/JLP-172)


### 1.0.87

***Implement email notifications***

* Add `email notification sending`
* Add `notifications resending` for admin panel

Task: [JLP-173](https://saritasa.atlassian.net/browse/JLP-173)


### 1.0.86

Improve DocuSign integration:

1. Restrict recipients full name length to 100 symbols.
2. Restrict ``esign`` S3 direct upload allowed mimetypes.
3. Restrict ``esign`` S3 direct upload allowed content length range.

Task: [JLP-286](https://saritasa.atlassian.net/browse/JLP-286)

### 1.0.85

***Update opportunities search logic***

`Opportunity` is now determined by this `logic`:

Topic is `opportunity` when `client`'s `state` is one of attorney's `practice` 
`jurisdiction`, and a `topic`'s `category` matches with attorney's `specialty` or 
`topic`'s `first post` or `title` contains `keywords` that are saved in `attorney`'s 
`profile`.

In other words:
```
If (
    client_state in attorney_practice_jurisdiction and 
    (
        client_specialty in attorney_specialty or (
            attorney_keywords in topic_title or in topic_first_post
        )
    )
):
    topic is opportunity for attorney
```

Task: [JLP-274](https://saritasa.atlassian.net/browse/JLP-274)


### 1.0.84

***Add basic notification workflow***

* Create `base` and `attorney` notification `resources`
* Create notification signal receiver, which depending on signal and instance 
creates `notification resource` and creates `dispatcher` which notifies `recipients`
* Update `Notification` model `content`(str) -> `content type` relation
* Update `NotificationDispatch` model `is_read` -> `status`
* Update `api` and `admin` panels
* Add `templates` for `new attorney event` notification
* Add `celery` task for `creating` and `dispatching` notifications

Task: [JLP-195](https://saritasa.atlassian.net/browse/JLP-195)

### 1.0.83

* Restrict `creation` of `lead` (`client` can be only a `user with client profile`)
* Add restriction for user `field` in `Attorney` and `Client` models(
so it would be possible to create `attorney` with `client profile` or `client` with 
`attorney profile` through admin panel)

Task: [JLP-278](https://saritasa.atlassian.net/browse/JLP-275)


### 1.0.82

Update Attorney Stripe profile API to provide possibility of changing
`payment_method`:

  - PUT, PATCH ``/api/v1/finance/profiles/current/`` with new `payment_method`.

Task: [JLP-275](https://saritasa.atlassian.net/browse/JLP-275)


### 1.0.81

Add API to get stripe profile data for current attorney:

  - GET ``/api/v1/finance/profiles/current/``

Task: [JLP-269](https://saritasa.atlassian.net/browse/JLP-269)


### 1.0.80

Add DocuSign webhook handling on Envelope `status` update.

1. When envelope is `sent` to signers after editing through edit link backend
app will catch a webhook and update original Envelope `status` to `sent` and
corresponding Matter's status to ``pending``.

2. When envelope is `completed` (signed by all signers) backend will catch a
webhook to update Envelope ``status`` to `completed` and corresponding Matter's
status to ``active``.

3. For all other Envelope statuses changes, only Envelope ``status`` will be
updated and Matter's status won't be changed.

4. Matter's status is changed only depending on its `initial` Envelope status
updates.

Also there is added a restriction on Matter validation - it is not allowed to
update matter's `esign_documents` for matters not in `draft` or `pending`
states.

When new Matter is created it always will have a ``draft`` status, so it will
be updated only when Attorney will send related Envelope through edit link.

Task: [JLP-208](https://saritasa.atlassian.net/browse/JLP-208)

### 1.0.79

* Now on `client register`, all `invites` that have it's `email`, will be updated to have a
`link to a new client`
* Make front-end template links `editable` in `admin` panel (also made `URLTemplateField`, so
nobody accidentally break backend parts that use that links.)

Task: [JLP-261](https://saritasa.atlassian.net/browse/JLP-261)


### 1.0.78

Add `keywords` ArrayField to Attorney model

* Add `keywords` to registration attorney (POST /users/attorney/)
* Extend `opportunities` queryset for topics - add filtering by keywords
* Add helper `convert_keywords_to_querytext`


Task: [JLP-221](https://saritasa.atlassian.net/browse/JLP-221)


### 1.0.77

Add ``name`` field to ESignDocument entity in swagger spec. Also added
possibility to set `Any Scheme` urls in DocuSign redirects
(`ReturnURL` and `RequiredReturnURL`). 

Task: [JLP-208](https://saritasa.atlassian.net/browse/JLP-208)


### 1.0.76

**Limit `chat creation`. `Attorney` and `client` can only have `one` chat.**

Task: [JLP-252](https://saritasa.atlassian.net/browse/JLP-252)


### 1.0.75

**Add filter for `/documents/` to get private resources for attorney**

Task: [JLP-251](https://saritasa.atlassian.net/browse/JLP-251)


### 1.0.74

* Add `STRIPE_ENABLED` settings 
* Disable creation subscription in verification attorney, if STRIPE_ENABLED = False
* Move creation customer in POST `/users/attorneys/` to service

Task: [JLP-63](https://saritasa.atlassian.net/browse/JLP-63)

### 1.0.73

Add possibility to update matter's and envelope's documents:

1. ``Matter`` entity in API now has 2 fields related to esigning:

    - `esign_documents` - write only field to update documents for esigning
    - `envelope_data` - data with `initial` Matter envelope

2. ``Envelope`` entity now has `documents` field with data DocuSign related
files, which can be editable,

Now it is available to update ``esign_documents`` in Matter, so if Matter's
Envelope was already sent - signers would get email that previous documetn set
signing was cancelled and new document set will be added.

If Matter's ``esign_documents`` shouldn't be changed - it shouldn't be set to
`null` or `[]` or can be not set at all.

Task: [JLP-238](https://saritasa.atlassian.net/browse/JLP-238)

### 1.0.72

Improve esign saving consent workflow:

- add Django Admin constance setting `BASE_OBTAIN_CONSENT_REDIRECT_URL` - it
will be used by `/esign/save-consent/` callback to redirect user to some
frontend url.

- add processing case when attorney not agrees on consent obtaining
(cancelled it) -> user will be redirected to request ``return_url`` or
``BASE_OBTAIN_CONSENT_REDIRECT_URL`` from Django Admin constance.

Task: [JLP-238](https://saritasa.atlassian.net/browse/JLP-238)

### 1.0.71

**Add separate api method for opportunities**

Task: [JLP-248](https://saritasa.atlassian.net/browse/JLP-248)


### 1.0.70

***Add invoice sending by email.***

Add `feature` to send `invoice`'s `pdf` file to client by using this `endpoint`:
* POST `business/invoices/{invoice_id}/send/`

Task: [JLP-245](https://saritasa.atlassian.net/browse/JLP-245)


### 1.0.69

**Change Matter's `stage` field's `on_delete` to `SET_NULL`**

Task: [JLP-244](https://saritasa.atlassian.net/browse/JLP-244)


### 1.0.68

***Add extra validation to Matter model***

* This `has_lead_with_user` filter filters queryset to return `attorneys`(or `clients`, depending on api)
that `client`(or `attorney`) has lead with `attorney`(or `client`)).
* Add extra validation for `Matter` model:
  * Check that Matter's `attorney` had a lead with `client`.
  * Check that Matter's `client` is a `client`(has a client profile)

Task: [JLP-239](https://saritasa.atlassian.net/browse/JLP-239)

### 1.0.67

Make ``esign_documents`` field not required in Matter (cause DocuSign
integration is not implemented yet). 

Task: [JLP-208](https://saritasa.atlassian.net/browse/JLP-208)

### 1.0.66

***Add info about attorney `verification` in `leads` and `matters`***

Add `AttorneyShortSerializer`, which has most important information about 
attorney:

* `id`
* `first_name`
* `last_name`
* `email`
* `phone`
* `avatar`
* `is_verified`
* `verification_status`
* `featured`
* `has_active_subscription`

Task: [JLP-230](https://saritasa.atlassian.net/browse/JLP-230)

### 1.0.65

Improve `esign` app API to provide `return_url` where it is needed:

1. GET `/esign/profiles/current/` - now this method can accept
`return_url` query parameter, which designates where user will be redirected
after obtaining consent (``return_url`` is saved to user ESignProfile after 
that), parameter is not required for this endpoint.

2. GET `/esign/envelopes/{id}/` and POST `/esign/envelopes/` - also now these
both methods accept ``return_url`` query_parameter too, which will designate
where user will be redirected after getting envelope `edit` view.

Task: [JLP-208](https://saritasa.atlassian.net/browse/JLP-208)

### 1.0.64

Add new API endpoints and extend existing ones to work with electronic signing:

- POST `/business/matters/` - extend endpoint with writable on create only
`esign_documents` field, which creates Envelope and send it in DocuSign

- GET `/esign/profiles/current/` - method allows to check if user already has
esign subscription to perform signing and returns an obtaining consent link
if it is needed

- GET `/esign/envelopes/`  - method to get all attorney's envelopes main info

- POST `/esign/envelopes/` - method to create new Envelope and receive its
`edit` view link (should be used on Documents creation)

- GET `/esign/envelopes/{id}/`  - method to get separate attorney's envelopes
details with ``edit_link`` field to edit Envelope in docuSign


Note: only one ``initial`` Envelope should exist withing Matter.


[Postman collection to work with API](https://www.getpostman.com/collections/bee9a44cfd01535081d0)


All webhooks will be implemented in separate tasks.

Task: [JLP-196](https://saritasa.atlassian.net/browse/JLP-196)

### 1.0.63

Add possibility to create draft Envelope in DocuSign and get its edit link.

Currently to test this behaviour there were added 2 buttons in Envelope Django
Admin:

- Create Draft Envelope
- Get Envelope Edit Link

Task: [JLP-158](https://saritasa.atlassian.net/browse/JLP-158)

### 1.0.62

Add ``esign`` app and its models for electronic signing with DocuSign:

- ESignProfile
- Envelope
- ESignDocument

Task: [JLP-177](https://saritasa.atlassian.net/browse/JLP-177)

### 1.0.61

Add ``DocuSignClient`` with possibility to perform impersonalization.

Task: [JLP-158](https://saritasa.atlassian.net/browse/JLP-158)
### 1.0.60

Add webhook handlers for stripe
* handle_subscription_payment_succeeded
* handle_subscription_payment_failed

Task: [JLP-199](https://saritasa.atlassian.net/browse/JLP-199)

### 1.0.59

Add `system.init-settings-local`, which loads all creds 
from `vault` and sets them in `settings` file.

Task: [JLP-187](https://saritasa.atlassian.net/browse/JLP-187)

### 1.0.58

**Add ability to edit `Matter`'s fields
(`city`, `state`, `country`, `rate`, `rate_type`, `title`, `description`, `code`) 
when Matter' status is `pending`**

Task: [JLP-229](https://saritasa.atlassian.net/browse/JLP-229)


### 1.0.57

***Fix `auth_password_change_create` error response***

Default drf `PasswordChangeSerializer` uses django's `ResetPasswordForm` which 
when validating new passwords use validate `clean_password2` method and because of that
response was like this:
```
"data": {
    "new_password2": [
        "This password is too short. It must contain at least 8 characters."
    ]
}
```
It was fixed to return `new_password1` instead `new_password2`

Task: [JLP-218](https://saritasa.atlassian.net/browse/JLP-218)


### 1.0.56

* Add to feature to set `closed` for Matter then this endpoint are used POST
`/business/matters/{id}/complete/`(this endpoint used when attorney wants to close matter)
* Improve Matter statuses endpoint `swagger` spec. Now they what they really need for request.
* Rename `closed` field in `Matter` model to `competed`

Task: [JLP-212](https://saritasa.atlassian.net/browse/JLP-212)


### 1.0.55

***Update data models and improve api performance***

* Add `unique_together` for `Matter` model -> `code` and `attorney`
* Add search by `first name` and `last name` for Invoice API
* Restrict editing on `Matter` through API(you can now change only `statuses`(separate `endpoints`) and `stages`)
* Improve `select_related` and `prefetch_related` queries for `Matter` API, `Lead` API, `Topic` API, `FollowedTopic` API
* Add queryset method `with followed`, which annotates Topic queryset with followed column(id of FollowedTopic)

Task: [JLP-190](https://saritasa.atlassian.net/browse/JLP-190)


### 1.0.54

***Improved permissions for attorney***

* Replace `IsAttorney` to `IsAttorneyFreeAccess`
* Replace `HasActiveSubscription` to `IsAttorneyHasActiveSubscription`
* Add `PlanProxyQuerySet` queryset
* Fix queryset in `PlanViewSet`

Task: [JLP-100](https://saritasa.atlassian.net/browse/JLP-100)


### 1.0.53

***Add `shared_folder` logic***

* Add `signal` which creates `new shared folder` for `matter`
* Add `IsNotSharedFolder` permission which checks if folder is shared or not
* `Forbid` folder creation inside shared folder
* `Forbid` shared folder `editing` and `deletion` through `API`
* `Forbid` creation of extra shared folders
* `Forbid` creation of shared folders without matter
* Improve `clean_title` method for `Folder` model
* Improve `clean` method for `BaseModel`

Task: [JLP-206](https://saritasa.atlassian.net/browse/JLP-206)


### 1.0.52

***Implement `search` for `attorney` by `location`***

* Add new fields for `Attorney` model
  * `firm_place_id` (CharField): Google identifier of place
  * `firm_location` (Point): Attorney's location coordinates
  * `firm_location_city` (CharField): Name of city, where attorney is located
  * `firm_location_state` (CharField): Name of state, where attorney is located
  * `firm_location_data` (JSONField):  All information about location from Google 
  stored as JSON 
* Add `queryset` to `Attorney`, that annotates `distance` between `attorney` and
`input coordinates`
* Update `AttorneyFactory` to set `location` fields for testing
* Update `Attorney Admin`, to show `map` with attorney `location` and ability to
`change location`(for `testing` purpose)
* Update `serializers` to include new attorney `location` fields
* Add `filtering` by states and cities in `AttorneyAPI`
* Add `ordering` by distance in `AttorneyAPI`
* Delete redundant `location fields` from `AppUser` model
* Add `state` and `state_data` fields to client serializer in business api

Task: [JLP-184](https://saritasa.atlassian.net/browse/JLP-184)


### 1.0.51

***Extend chats functionality***

* Allow `clients` to create `Leads` through `API`.
* Add chat statistics creation in `firebase` when new Lead is created.
* Update `firebase rules`
  * User can now `update` chats statistics if user is participant of this chat
  * Rename `posts` to `messages`
* Update `firebase docs`

Task: [JLP-207](https://saritasa.atlassian.net/browse/JLP-207)


### 1.0.50

***Add creation initial subscription for Attorney***

* Add `has_active_subscription` to `AppUser`
* Add `FinanceProfile` model 
* Add service `create_initial_subscription`
* Update `decline` and `verify` process in Attorney
* Add checking type `PlanProxy` via metadata 
* Add `create_attorney_subscription` to `Attorney.verify_by_admin`
* Add cached_property `customer` for User
* Update `HasActiveSubscription` - disabled for development

Task: [JLP-186](https://saritasa.atlassian.net/browse/JLP-186)

### 1.0.49

***Add permission for checking attorney subscription status***

* Added `IsAttorneyHasActiveSubscription` permission and set in attorneys endpoints
Apply `IsAttorneyHasActiveSubscription` to these endpoints:
* `/api/v1/users/attorneys/current/ ` CurrentAttorneyView
* `/users/attorneys/current/statistics/current/` StatisticsAttorneyView
* `/api/v1/business/leads/` LeadViewSet
* `/api/v1/business/matters/` MatterViewSet
* `/api/v1/business/billing-items/` BillingItemViewSet
* `/api/v1/promotion/events/` EventViewSet
* `/api/v1/business/invoices/` InvoiceViewSet
* `/api/v1/business/activities/` ActivityViewSet
* `/api/v1/business/notes/` NoteViewSet
* `/api/v1/business/checklist/` ChecklistEntryViewSet
* `/api/v1/business/stages/` StageViewSet

Task: [JLP-100](https://saritasa.atlassian.net/browse/JLP-100)

### 1.0.48

Remove `practice_area` field from `Attorney` model

Task: [JLP-191](https://saritasa.atlassian.net/browse/JLP-191)

### 1.0.47

*`Forbid` creation of attorney with no `specialties`.*

Task: [JLP-198](https://saritasa.atlassian.net/browse/JLP-198)

### 1.0.46

*Add old password field for password change serializer by adding this to `drf` settings:*
```
OLD_PASSWORD_FIELD_ENABLED = True
```

Task: [JLP-197](https://saritasa.atlassian.net/browse/JLP-197)


### 1.0.45

Provide API for messages between attorney and client inside matter.

Add CRUD API for MatterTopic model with additional post creation method.

Task: [JLP-150](https://saritasa.atlassian.net/browse/JLP-150)


### 1.0.44

***Add total fees and total time calculation***

* Update GET /business/time-billing/ endpoint to return 
additional information
* Provide inspector for correct swagger generation.

Task: [JLP-175](https://saritasa.atlassian.net/browse/JLP-175)

### 1.0.43

***Extend registration attorneys - POST `/users/attorneys/`***

* Removed `IsAuthenticated` from GET `/finance/subscribe/get-setup-intent/ `
* Removed POST `/finance/subscribe/create-subscription/` 
* Moved the step of creating a customer to POST `/users/attorneys/`, updated `AttorneyRegisterSerializer`
* Added `CustomerProxy`model
* Fixed `test_register_attorney_api` test 
* Provided GET `/test-subscription/` *AttorneyRegistrationTestView* (old `UserSubscriptionDetailView)` for full test registration
* Added `AttorneyCustomerError`
* Fixed CLI creation products and plans for testing purpose
* Added `description` to GET `/finance/plans/`

Task: [JLP-161](https://saritasa.atlassian.net/browse/JLP-161)

### 1.0.42

***Add `statistics` endpoints for `attorney`(for attorney dashboard)***

* Add `services` for attorney, which calculates `current​` statistics and
statistics for `time period`
* Add `filter` for `Topic` model (for `following` and `opportunities`)
* Add `serializers` for `swagger` specs
* Add API endpoint for retrieving `current​ statistics` and `statistics for
quarter`

**New endpoints**

* GET `/users​/attorneys​/current​/statistics​/current​` - Get attorney's `statistics` for dashboard(
count leads, matters, opportunities and documents)
* GET `/users/attorneys/current/statistics/period` - Get attorney's `statistics` for time period(
time billed stats for now
)

Task [JLP-168](https://saritasa.atlassian.net/browse/JLP-168)


### 1.0.41

***Update `attorney` model***

* Add `phone` number
* Make `practice_jurisdiction` into `practice_jurisdictions` 
(M2M to support multiple states)
* Update `admin panel` and `API`.

Task: [JLP-176](https://saritasa.atlassian.net/browse/JLP-176)


### 1.0.40

***Fix category icon upload***

* Add `upload path` for category icons
* Add `icon display` for category admin panel
* Add `autocomplete fields` for forums app admin panels
* Add icon generation to `CategoryFactory`

Task: [JLP-179](https://saritasa.atlassian.net/browse/JLP-179)


### 1.0.39

**Add action for `Lead` admin to sync Firebase DB**

* Added helper methods in channels.py
  * `delete_redundant_users`(
    Delete users from FireBase that doesn't exist in backend db.
  )
  * `delete_redundant_lead_chats`(
    Delete leads' chats form FireBase that doesn't exist in backend db.
  )
  * `delete_user`(
    Delete user's chats and it's info from firebase.
  )
  * `delete_all_user_chats`(
    Delete all user's chats.
   )
  * `delete_redundant_user_chats`(
    Delete users' chats from FireBase that doesn't exist in db.
   )
* Extended docs and annotated methods for `FirestoreClient` class

Task: [JLP-157](https://saritasa.atlassian.net/browse/JLP-157)


### 1.0.38

**Improve `system.init-firebase-local` script**

* Improve `system.init-firebase-local` to get all credentials for firebase from one 
`vault` storage
* Remove redundant `init_settings.py`
* Update `settings` and `template` for `local settings`
* Improve `firebase` invoke commands errors messages

Task: [JLP-165](https://saritasa.atlassian.net/browse/JLP-165)

### 1.0.37

Add ``fees_earned`` field to Matter entity.

Task [JLP-108](https://saritasa.atlassian.net/browse/JLP-108)


### 1.0.36

Update CitySerializer to create new city if no Id was provided.

Affected endpoints: 

* POST - `/users/attorneys/`
* POST - `/business/matters/`


Task [JLP-163](https://saritasa.atlassian.net/browse/JLP-163)

### 1.0.35

**Set up `invite` workflow**

* Add template for `invitation email`
* Add notification `InviteNotification`
* Set up `post_save` signal for `Invite`, which sends `invitation email` to client
* Fix `permissions` for `InviteViewSet`
* Update client registration `serializer` to use invite model(if invite `uuid` was passed 
on register, serializer will assign `new user` to `invite`)

Task: [JLP-97](https://saritasa.atlassian.net/browse/JLP-97)

### 1.0.34

1. Add API method to generate Invoice PDF:
GET `/api/v1/business/invoices/{invoice}/export/`

2. Add celery task, which generates Invoice every 1st day of a month for the
previous month period for `active` matters with `hourly` rate type. All time
billings related to Invoice period will be added.

3. Also added a signal to update existing or create new Invoice for a new
BillingItem creation for an old period. 

So if new time billing is created with a date for already passed periods:
  
  - try to find existing invoice for the period and update it (add this time
  billing to it).
  
  - if no existing invoice was found - generate new invoice with created time
  billing.

If time billing is created for current period or a future period - do nothing
and let app generate invoice by itself when time comes (at the 1st day of a
new period month). 

Task: [JLP-98](https://saritasa.atlassian.net/browse/JLP-98)

### 1.0.33

***Restrict creation of notification setting with wrong recipient type***

Add `validation` that checks that `recipient type` on creation of 
`notification setting` corresponds to the current user's type
* `Attorney` - attorney, all
* `Client` - client, all

Make `notifications/types/` endpoint return `notification types` available 
for current user

Task: [JLP-162](https://saritasa.atlassian.net/browse/JLP-162)


### 1.0.32

***Add CRUD API for `Note` model***

* Add `NoteSerializer` and `UpdateNoteSerializer`
* Add CRUD API `view set` for Notes model
* Set up `permissions` for Notes API
* Add `filter` for Notes view


Task: [JLP-126](https://saritasa.atlassian.net/browse/JLP-126)


### 1.0.31

**Add `ChecklistEntry` model and API view (`/business​/checklist/`)**

* Add `ChecklistEntry` model
* Add factory and admin ui for `ChecklistEntry` model 
* Add API View

*New endpoints*:

* GET `/business​/checklist/` - get all attorney's checklist entries
* POST `/business​/checklist/` - create new checklist entry
* PUT `/business​/checklist/{id}` - update checklist entry
* PATCH `/business​/checklist/{id}` - update checklist entry
* DELETE `/business​/checklist/{id}` - delete checklist entry

Task: [JLP-145](https://saritasa.atlassian.net/browse/JLP-145)


### 1.0.30

**Update user app API**

* Forbid user to edit first name, last name and email address
* Make email field visible in clients api

Task: [JLP-124](https://saritasa.atlassian.net/browse/JLP-124)


### 1.0.29

Add `AppUser` email export by `django-import-export`

Task: [JLP-96](https://saritasa.atlassian.net/browse/JLP-96)

### 1.0.28

***Add CRUD features for documents api***

* Add `CRUD` for `Folders`(improve serializers and add update serializers)
* Add `CRUD` for `Documents`(improve serializers and add update serializers)
* Add duplicate feature for `Documents` API
* Add extra validations for `Resources` models
* Set up `S3` direction

Task: [JLP-62](https://saritasa.atlassian.net/browse/JLP-62)


### 1.0.27

***Add Read only `Documents` app API***

* Add `Document` and `Folder` object `serializers`
* Add read only resource view for `Document` and `Folder` models
* Set up filters for resource view 
* Add read only views for `Documents` and `Folders` models

Task: [JLP-62](https://saritasa.atlassian.net/browse/JLP-62)


### 1.0.26

***Add Documents app***

* Add models: `Folder`, `Document`
* Add `factories` for new models
* Add `admin` panels

Task: [JLP-62](https://saritasa.atlassian.net/browse/JLP-62)


### 1.0.25

Extend search and ordering for Topic viewset 

Add `FollowedTopics` view for topic follow

* GET `forum/followed/` - get all user followings
* POST `forum/followed/` - follow new topic
* DELETE `forum/followed/{id}` - unfollow topic

Task: [JLP-70](https://saritasa.atlassian.net/browse/JLP-70)


### 1.0.24

1. Removed code to creation test plans and product. Moved to CLI `create_product_and_plans`
2. Updated `PlanProxyAdmin` and `ProductProxyAdmin`
    * Creation these object via admin are work
    * Prevent changes via admin 
    * Restricted `product` removal

Task: [JLP-99](https://saritasa.atlassian.net/browse/JLP-99)

1. Add model: SubscriptionProxy
2. Update POST ``/api/v1/finance/subscribe/create-subscription/``
* Support 3d secure card with immediately charges
* Added logging of errors

Task: [JLP-94](https://saritasa.atlassian.net/browse/JLP-94)

### 1.0.23

Setup Firebase related permissions rules and placed them in 
``artifacts/firestore-rules.js``, added explanation and docs for these files.

Task: [JLP-105](https://saritasa.atlassian.net/browse/JLP-105)

### 1.0.22

Add Firebase related signals on backend:

1. When new Lead is created - there is created a new chat channel in Firebase

2. When Lead is deleted - corresponding chat is totally removed from
Firebase + there is removed chat related statistics for users.

Firebase Structure with all explanations is placed in docs ``firebase.md``.

Task: [JLP-103](https://saritasa.atlassian.net/browse/JLP-103)


### 1.0.21

Add base stuff for Firebase `firestore` integration on backend:

- Firestore client (which makes login in Firestore, gets and creates needed data)

- API to get Firestore credentials token for frontend 
  (GET `/api/v1/firestore/get-credentials/` - available for authorized users only)

- corresponding settings and requirements

- `system.init-firebase-local` invoke command (to get firebase credentials 
  in local)
  
- updated Jenkins build (so on project deploy firebase credentials would be get)

Task: [JLP-103](https://saritasa.atlassian.net/browse/JLP-103)


### 1.0.20

***Update business app***

**Models updates**:
* Update business models
* Update business admins and factories
* Improve factories

***Add API improvements***:
* Fix permissions for BaseViewSetMixin
* Add filter for invoice api (by `period`)
* Add `client` to InvoiceSerializer
* Add `status` to InvoiceSerializer
* Add amount of billed time for `matter`
* Add `Activity` api viewset (`/business​/activities​/`)
* Add `Stage` api viewset (`/business​/stages/`)
* Add clean method for stage field in Matter model
* Refactor serializers for auto api docs

Task: [JLP-73](https://saritasa.atlassian.net/browse/JLP-73)


### 1.0.19

Add `Promotion` app

* Add `Event` model
* Add `admin panel` for events
* Add events `factory`
* Add `api` view for events and set up `permissions` and `filters`

`Promotion` app endpoints for `event` model 
(`CRUD` for `attorneys` and `read only` for `clients`):

* GET `promotion/events/`  - get all events
* GET `promotion/events/{id}` - get one event
* POST `promotion/events/{id}/` - create event
* PUT `promotion/events/{id}/` - update event
* PATCH `promotion/events/{id}/` - update event
* DELETE `promotion/events/{id}/` - delete event

Task: [JLP-74](https://saritasa.atlassian.net/browse/JLP-74)


### 1.0.18

Add `user_type` to default token serializer

Task: [JLP-95](https://saritasa.atlassian.net/browse/JLP-95)


### 1.0.17

***Update users app***
* Update users models
* Add `Client` factory
* Update user's admin panel
* Remade `Client` registration
* Add `filter` for users
* Refactoring of registration serializers
* Fix and update tests
* `Clients` endpoints moved to `users/clients`

Task: [JLP-86](https://saritasa.atlassian.net/browse/JLP-86)


### 1.0.16

Add `stripe` integration through `djstripe` package.

Add API methods to work with Stripe:

1. GET ``/api/v1/finance/subscribe/get-setup-intent/`` - method should be
called before subscription creation to prepare SetupIntent.

2. POST ``/api/v1/finance/subscribe/create-subscription/`` - method should be 
used to create user subscription.

Also for testing purpose there was added simple django page, which makes user
subscription creation (cause frontend is not ready yet):

GET ``/user-subscription/``.

This approach doesn't work with 3D secure cards yet.

Task: [JLP-63](https://saritasa.atlassian.net/browse/JLP-63)


### 1.0.15

Simplify attorney registration:

* Make attorney's `address_city`, `address_city`, `address_zip` fields not required

* Remove validation for attorney `address_city` and `address_state`

Task: [JLP-82](https://saritasa.atlassian.net/browse/JLP-82)


### 1.0.14

Add `notifications` API endpoints

Endpoints for `NotificationDispatch` (can only read and update):
* GET `/notifications/`
* GET `/notifications/{id}/`
* PUT `/notifications/{id}/`
* PATCH `/notifications/{id}/`

Endpoints for `NotificationSetting` (can only read, create and update):
* GET `/notifications/settings/`
* POST `/notifications/settings/` (create and update)
* GET `/notifications/settings/{id}/`
 
Endpoints for `NotificationType` (read only):
* GET `/notifications/types/`
* GET `/notifications/types/{id}/`
 
Endpoints for `NotificationGroup` (read only):
* GET `/notifications/groups/`
* GET `/notifications/groups/{id}/`

Task: [JLP-68](https://saritasa.atlassian.net/browse/JLP-68)


### 1.0.13

Add `notifications` app

Add models:
* `Notification`
* `NotificationDispatch`
* `NotificationType`
* `NotificationGroup`
* `NotificationSetting`

Made `factories` for these models

Set up `admin` panels for `notifications` app

Task: [JLP-67](https://saritasa.atlassian.net/browse/JLP-67)


### 1.0.13

Simplify attorney registration:

* Make attorney's `address_city`, `address_city`, `address_zip` fields not required

* Remove validation for attorney `address_city` and `address_state`

Task: [JLP-82](https://saritasa.atlassian.net/browse/JLP-82)


### 1.0.12

Add endpoint for generating upload params for JusLaw S3 bucket.

* GET `/s3direct/get_params/`

Delete redundant endpoints:

* POST `/users/current/avatar/`
* DELETE `/users/current/avatar/`

Task: [JLP-47](https://saritasa.atlassian.net/browse/JLP-47)


### 1.0.11

***Update `users` app models***:

**AppUser:**
* Remove `phone` field
* Change `location` field to `PointField`
* Add `location_title` (str) field
* Add new model `Invite`

**Attorney**
* Replace `experience_years`(int) -> `employment_year`(int)
* Add `followers` field (m2m link between `Attorney` and `AppUser`)

**AttorneyEducation**
* Remove `degree` field 

***API updates and improvements***:

* Add filters by `featured` and `followed` in `attorney` api
* Add `Follow/Unfollow` endpoint feature to api
  * POST `/users/attorneys/{user}/follow/` to follow `attorney`
  * POST `/users/attorneys/{user}/unfollow/` to unfollow `attorney`
* Update `AttorneyEducationSerializer`, now it accepts `university` as string
(title of `university`)
* Add filter `UniversityFilter`, allows it filter `universities` by their 
title(`istartswith`)
* Add Viewset for `Invite` model at `users/invites`

Task: [JLP-66](https://saritasa.atlassian.net/browse/JLP-66)


### 1.0.10

Fix password reset in api (fixed by changing `default_token_generator` 
to `EmailAwarePasswordResetTokenGenerator` from `all_auth` package)

Remove GET `/auth/logout` endpoint

Redefine default `drf` auth views to improve docs for `drf-yasg`

Task: [JLP-78](https://saritasa.atlassian.net/browse/JLP-78)

### 1.0.9

Add `celery` task that executed every day and updates `django-cities-light` database.

Also add invoke command(to update `django-cities-light` database) for development.

Limit load of cities in local settings.

Task: [JLP-39](https://saritasa.atlassian.net/browse/JLP-39)


### 1.0.8

Fix issue with `CSRF` errors raising in user login through API.

Task: [JLP-64](https://saritasa.atlassian.net/browse/JLP-64)

### 1.0.7

Add `Attorney` verification logic. After user submitted it's `Attorney` profile, 
it's account becomes inactive until it's `Attorney` profile is approved by admins.

Add admin buttons for verification of attorneys

Add verification notifications:
* `Attorney` will get an email about `Verification Approved` or `Denied`
(Attorney get notifications every time admin change it's verification status)
* Admins will get an email about a new `Attorney`
(Admins get notifications every time new attorney is created)

Change `is_verified` to `verification_status` in `Attorney` model, 
there three statuses:

* `not_verified` - Default on submission
* `approved` - Approved by admins
* `denied` - Denied by admins

Task: [JLP-37](https://saritasa.atlassian.net/browse/JLP-37)

### 1.0.6

***Add API endpoints for `business` app:***

**Lead**:
- ``/business/leads/`` - GET (client, attorney), POST (attorney)
- ``/business/leads/{id}/`` - GET (client, attorney), PATCH (attorney), PUT
(attorney), DELETE (attorney)


**Matter**:
- ``/business/matters/`` - GET (client, attorney), POST (attorney)
- ``/business/matters/{id}/`` - GET (client, attorney), PATCH (attorney), PUT
(attorney), DELETE (attorney)
- ``/business/matters/{id}/activate/`` - POST (attorney)
- ``/business/matters/{id}/pending/`` - POST (attorney)
- ``/business/matters/{id}/revoke/`` - POST (attorney)
- ``/business/matters/{id}/complete/`` - POST (attorney)


**BillingItem**:
- ``/business/billing-item/`` - GET (client, attorney), POST (attorney)
- ``/business/billing-item/{id}/`` - GET (client, attorney), PATCH (attorney),
PUT (attorney), DELETE (attorney)


**Invoice**:
- ``/business/invoices/`` - GET (client, attorney), POST (attorney)
- ``/business/invoices/{id}/`` - GET (client, attorney), PATCH (attorney),
PUT (attorney), DELETE (attorney)


***For all this endpoints there are returned different results depending on
request user (if he is client or not):***

- `client` - get only instances where he is a client (lead, matter) or
matter client (time-billing, invoices) - read only permissions
- `attorney` - get only instances where he is an attorney (lead, matter) or
matter attorney (time-billing, invoices) - CRUD permissions

Task: [JLP-31](https://saritasa.atlassian.net/browse/JLP-31)

### 1.0.5

Add serializers for `forums` app model:

- `Post` model
- `Category` model
- `Topic` model

Add following endpoints:

* GET `/forum/categories/` Retrieve list of available forum categories
* GET `/forum/categories/{id}/` Retrieve single forum category

* GET `/forum/posts/` Retrieve list of available forum posts
* POST `/forum/posts/` Create new post on forum 
* GET `/forum/posts/{id}/` Retrieve single post from forum

* GET `/forum/topics/` Retrieve list of available forum topics
* POST `/forum/topics/` Create topic on forum
* GET `/forum/topics/{id}/` Retrieve single topic on forum

Extend `AppUserSerializer` with `UserStats` data. 

Create `forums` app models:

- Category
- FollowedTopic
- UserStats

Update `forums` app models:

- Topic
- Post

Add admin UI for new models and update UI for existent ones.  

### 1.0.4

Refactor `users` app api endpoints:

`Auth`

* `/auth/login`/ - POST
* `/auth/logout/` - GET, POST
* `/auth/password/change/` - POST
* `/auth/password/reset/` - POST
* `/auth/password/reset/confirm/` - POST

`AppUsers`

* `/users/` - GET, POST (register new client user)
* `/users/{id}/` - GET
* `/users/current/` - GET, PUT, PATCH for current client user
* `/users/current/avatar/` - POST, DELETE for current client user

`Attorney`

* `/users/attorneys/` - GET, POST (register attorney)
* `/users/attorneys/{id}/` - GET
* `/users/attorneys/current/` - GET, PUT, PATCH for current attorney

`Attorney links`

* `/users/fee-kinds/` - GET
* `/users/fee-kinds/{id}/` - GET
* `/users/specialties/` - GET
* `/users/specialties/{id}/` - GET
* `/users/universities/` - GET
* `/users/universities/{id}/` - GET

Task: [JLP-46](https://saritasa.atlassian.net/browse/JLP-46)

### 1.0.3

Create `business` app models:

- Invoice
- Lead
- Matter
- BillingItem
- Note
- Activity

Create templates for `forums` app models:

- Topic
- Post

Task: [JLP-30](https://saritasa.atlassian.net/browse/JLP-30)

### 1.0.2

Set up `Attorney` model  and it's links models `AttorneyEducation`, `FeeKind`, `Speciality`, `University`.
Separate `AppUser` into two parts: one for current user(retrieve and update) and other is for retrieval and 
for search of users' profiles(read only).

For retrieving and editing current user's profile:
* GET `/account/user` Get user's basic info
* PUT `/account/user` Update user's info
* PATCH `/account/user` Update user's info(partial)

For uploading and deleting user's avatar:
* POST `/account/avatar` Upload user's avatar
* DELETE `/account/avatar` Delete user's avatar

For creating, retrieving and editing user's attorney profile:
* GET `/account/attorney` Get current user's attorney profile
* POST `/account/attorney` Create attorney profile for current user
* PUT `/account/attorney` Update attorney profile
* PATCH `/account/attorney` Update attorney profile(partial)

Endpoints for retrieval and for search of users(read only):
* GET `/users/app-users/` Get list of users
* GET `/users/app-users/{id}` Get user's basic info

Endpoints for retrieval and for search of users' attorney profiles(read only):
* GET `/users/attorney/` Get list of attorneys
* GET `/users/attorney/{user}/` Get attorneys information

`FeeKind`, `Speciality`, `University` models endpoints(also search by title is available):
* GET `/users/fee-kinds/` Get list of fee kinds
* GET `/users/fee-kinds/{id}` Get fee kind
* GET `/users/specialities/` Get list of specialities
* GET `/users/specialities/{id}` Get speciality
* GET `/users/universities/` Get list of universities
* GET `/users/universities/{id}` Get university

Add endpoints for retrieval location models(also search by name is available):
* GET `/locations​/cities​/` Get list of Cities
* GET `/locations​/countries​/` Get list of Countries
* GET ​`/locations​/states/` Get list of States (regions)

Task: [JLP-28](https://saritasa.atlassian.net/browse/JLP-28)

### 1.0.1

Add authentication endpoints.

Set up `AppUser` model and it's endpoints

Authentication endpoints:
* POST `/auth/login`
* GET `/auth/logout`
* POST `/auth/logout`
* POST `/auth/password/change`
* POST `/auth​/password​/reset`
* POST `/auth/password/reset/confirm`
* POST `/auth/register/attorney`
* POST `/auth/register/client`

AppUser endpoints:
* GET `/users/` Get list of users
* GET `/users/{id}` Get user's basic info
* PUT `/users/{id}` Update user's info
* PATCH `/users/{id}` Update user's info(partial)
* POST `/users/avatar` Upload user's avatar
* DELETE `/users/avatar` Delete user's avatar

Task: [JLP-27](https://saritasa.atlassian.net/browse/JLP-27)

### 1.0.0

Project initialised

Task: [JLP-18](https://saritasa.atlassian.net/browse/JLP-18)
