import arrow

from config.celery import app

from . import models


@app.task()
def cancel_failed_payments():
    """Celery task to cancel failed payments.

    If payment is failed for more than a day we cancel it.

    """
    day_ago = arrow.utcnow().shift(days=-1)
    failed_payments = models.Payment.objects.filter(
        status=models.Payment.STATUS_FAILED,
        modified__lte=day_ago.datetime
    )
    for payment in failed_payments:
        payment.cancel_payment()
