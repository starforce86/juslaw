# turn on stripe for production environment only
STRIPE_LIVE_MODE = False
# A version of API used by webhook
STRIPE_WEBHOOK_VERSION = '2019-10-08'
# by default creation stripe objects are enable
STRIPE_ENABLED = True

# the way how coming to app webhooks are validated (for security reasons)
# should be always `verify_signature`, cause `retrieve_event` verification
# wouldn't work for stripe connect API (stripe connect events couldn't be
# found in all webhooks Events API, they are connected to `connected accounts`)
DJSTRIPE_WEBHOOK_VALIDATION = 'verify_signature'
DJSTRIPE_WEBHOOK_SECRET = None
DJSTRIPE_WEBHOOK_URL = r"webhook/$"

# Settings related to Stripe connect
STRIPE_CONNECT_CLIENT_ID = None
STRIPE_BASE_AUTH_ERROR_REDIRECT_URL = None
DJSTRIPE_CONNECT_WEBHOOK_SECRET = None
