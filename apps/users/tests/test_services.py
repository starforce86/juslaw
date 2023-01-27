import pytest
from constance import config

from ...finance.models import Payment
from .. import factories, models, services


@pytest.mark.usefixtures('stripe_create_payment_intent')
def test_get_or_create_support_fee_payment():
    """Test get_or_create_support_fee_payment function

    Test that get_or_create_support_fee_payment creates payment for
    support.

    """
    support: models.Support = factories.SupportVerifiedFactory()
    payment = services.get_or_create_support_fee_payment(support=support)
    # Check that payment was correctly created
    assert payment
    assert payment.status == Payment.STATUS_IN_PROGRESS
    assert payment.amount == config.PARALEGAL_USER_FEE
    assert payment.recipient_id is None
    assert payment.payer_id == support.pk
    assert payment.application_fee_amount == 0.0
