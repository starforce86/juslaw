import logging

from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from ...models import WebhookEventTriggerProxy

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class ProcessWebhookView(View):
    """Almost original `djstripe` Webhook handler view.

    The only difference is that current overridden view works with
    WebhookEventTriggerProxy model instead of original WebhookEventTrigger. It
    is needed to allow usage of separate webhook secret for Stripe Connect
    webhooks. So now simple webhooks use `DJSTRIPE_WEBHOOK_SECRET` for
    validation (subscriptions workflow) and connect webhooks use
    `DJSTRIPE_CONNECT_WEBHOOK_SECRET` (direct deposits workflow).

    """

    def post(self, request):
        if "HTTP_STRIPE_SIGNATURE" not in request.META:
            # Do not even attempt to process/store the event if there is
            # no signature in the headers so we avoid overfilling the db.
            return HttpResponseBadRequest()

        # the only difference is here
        trigger = WebhookEventTriggerProxy.from_request(request)

        if trigger.is_test_event:
            # Since we don't do signature verification, we have to skip
            # trigger.valid
            return HttpResponse("Test webhook successfully received!")

        if not trigger.valid:
            # Webhook Event did not validate, return 400
            return HttpResponseBadRequest()

        return HttpResponse(str(trigger.id))
