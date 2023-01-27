# Notifications

## Notification description

### Notifications types

#### All (or common) notifications

* `new_message` - This `notification` is sent when `attorney` or `client`
creates a `new post` in matter's `topic`. In designs it's `New Message`
notification type of of group `Matters`.

* `new_chat` - This `notification` is sent to `attorney` or `client` when
creator of lead creates `lead` with this `attorney` or `client`. In designs
it's `New Chats` notification type.

#### Attorney notifications

* `new_opportunities` -  This `notification` is sent every day to attorney,
if there were any new opportunities created for this attorney on that day.
In designs it's `New Opportunities` notification type.

* `new_matter_shared` - This `notification` is sent when a matter of another
attorney becomes `shared` with current attorney user for a first time. In
designs it's `New Matter Shared` notification type.

#### Client notifications

* `new_attorney_event` - This `notification` is sent to attorneys' `followers`,
when attorney creates `new event`. In designs it's `New Event` notification
type of group `Attorneys I Follow`.

* `new_attorney_post` - This `notification` is sent to attorneys' `followers`,
when attorney creates `new post` in forums. In designs it's `Forum Activity`
notification type of group `Attorneys I Follow`.

* `new_post` - This `notification` is sent to topic' `followers`, when somebody
creates `new post` in this topic. In designs it's `Topics I Follow Activity`
notification type.

* `matter_status_update` - This `notification` is sent to `client` when
attorney changes status of client's matter. In designs it's `Status Update`
notification type of group `Matters`.

* `document_shared_by_attorney` -  This `notification` is sent to client when
`attorney` uploads `file to shared folder`. In designs it's `File Shared`
notification type of group `Matters`.

#### Support notifications

* `new_matter_shared` - This `notification` is sent when a matter of attorney
becomes `shared` with current support user for a first time. In designs
it's `New Matter Shared` notification type.

#### Additional notifications

* `Admins` get notifications every time `new attorney is created`

* `Attorney` get notifications every time admin changes `attorney`'s
`verification status`

### Notification dispatching

User can receive notification by push(firebase messaging), by email or view it
app itself(by using api endpoint `api/v1/notifications/`). `User` receives
`notification` only when user has `settings` for this notification's `type` 
and this settings has email or push notifications turn on (`by_push` or
`by_email` == `True`).


### Device registration for push notifications

You can register device for push notification by using this endpoint
`/api/v1/fcmdevices/`(also `edit`, `retrieve` and  `delete`).

* `registration_id` (required) - Firebase Token of device.
* `name` (optional) - name of device.
* `active` (default: true) - if device is marked as `non-active`, it `won't`
receive any notifications. Also if backend can't deliver push notification,
it will mark device as `non-active`.
* `device_id` (optional - can be used to uniquely identify devices) - you can
set id of device if needed, backend doesn't use it.
* `type` (`android`, `web`, `ios`) - type of device.

### Test device registration and push notification

After you registered your device you can test registration by visiting admin
panel for fcm devices (`/admin/fcm_django/fcmdevice/`). Mark your device and
select an action(`Send test notification` or `Send test data message`). It will
display you results of push(and `errors` if there are any) and also send push 
notification to your device.

## Implementation notes

### Notification resources

This classes specifies, `how to work` with certain `notification type`
(by using `runtime tag`). In resource class `you must`  specify the following:

* `runtime_tag` - runtime_tag of notification type.
* `signal` - A signal to which notification responds.
* `instance_type` - Model class with which resource can work with.
* `title` - Notification's title.
* `web_content_template` - Path for notification content `template` that will
be used by `frontend team`.
* `push_content_template` - Path for push notification's `template`. Used in
`push notifications` send by `firebase`.
* `email_content_template` - Path to html `template` for email notification's
content. Used for creating `html content`  for `email notifications`.
* `get_recipients` - Add logic of how `resource class` should get
notification's `recipients` from `instance` (instance that triggered
notification).

You can also `override` this `methods`:
* `prepare_payload` - used to create `context` for `templates`
* `get_web_notification_content` - renders content for `frontend team`
* `get_push_notification_content` - renders content for `push notification`
* `get_email_notification_content` - renders content for `email notification`

### Triggering

Function `generate_and_send_notification` in `signals.py` of notification app,
is  responsible of catching all `signals`, that requires notification creation.
It listens to a `signal` and `sender` specified in `notification resource`.
After receiving a signal it sends data to celery task `send_notifications`.

### Notification creation (celery task `send_notifications`)

`send_notifications` creates notification in database and uses `resource` and
`notification` to create instance of  `NotificationDispatcher`, which then
creates `notification dispatches` and `sends notifications`.

### Dispatching (`NotificationDispatcher` class)

`Dispatching of notifications` starts by calling method `notify` of
`NotificationDispatcher`. This method first creates `notification dispatchers`
for `recipients`(by using notification resource and checking if
`potential recipient` has `enabled settings` for `notification type` of
notification resource). Then by using created `notification dispatches`, 
it sends email or push notifications.
