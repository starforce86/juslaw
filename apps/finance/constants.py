# Usage for initial subscriptions
PROMO_PERIOD_MONTH = 6


class PlanTypes:
    """Enum of subscription plan types for PlanProxy model."""
    PREMIUM = 'premium'
    STANDARD = 'standard'


class Capabilities:
    """Enum of requested by app account privileges for Stripe connect API.

    https://stripe.com/docs/connect/account-capabilities

    """
    CAPABILITY_CARD_PAYMENTS = 'card_payments'
    CAPABILITY_TRANSFERS = 'transfers'
    CAPABILITY_TAX_REPORTING_US_1099_MISC = 'tax_reporting_us_1099_misc'
    CAPABILITY_TAX_REPORTING_US_1099_K = 'tax_reporting_us_1099_k'

    default = [
        CAPABILITY_CARD_PAYMENTS,
        CAPABILITY_TRANSFERS,
        CAPABILITY_TAX_REPORTING_US_1099_MISC,
        CAPABILITY_TAX_REPORTING_US_1099_K
    ]
