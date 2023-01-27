from datetime import timedelta

import arrow
import pytest
from constance import config

from libs.utils import get_datetime_from_str

from apps.business.notifications import InvoiceEmailNotification
from apps.finance.models import Payment
from apps.users.models import AppUser

from ... import factories, models
from ...services import invoices as services

get_invoice_period_data = [
    # case when invoice period is formatted as month, equality is tracked by
    # month and months are the same-> no duplicates should be in result `Sep`
    (
        get_datetime_from_str('2018-09-12'),
        get_datetime_from_str('2019-09-12'),
        '%b', 'month', 'Sep'
    ),
    # case when invoice period is formatted as month and equality is not
    # tracked at all -> result will have duplicates `Sep - Sep`
    (
        get_datetime_from_str('2018-09-12'),
        get_datetime_from_str('2018-09-12'),
        '%b', None, 'Sep - Sep'
    ),
    # case when invoice period is formatted as year and equality is tracked by
    # year and years are different -> no duplicates should be in result
    # `2018 - 2019`
    (
        get_datetime_from_str('2018-09-12'),
        get_datetime_from_str('2019-09-12'),
        '%Y', 'year', '2018 - 2019'
    ),
]


@pytest.mark.parametrize(
    'period_start,period_end,date_format,equality_attr,expected_result',
    get_invoice_period_data
)
def test_get_invoice_period_str_representation(
    matter, period_start, period_end, date_format, equality_attr,
    expected_result
):
    """Test for `get_invoice_period_str_representation` method."""
    invoice = factories.InvoiceFactory(
        period_start=period_start,
        period_end=period_end,
        matter=matter
    )
    result = services.get_invoice_period_str_representation(
        invoice=invoice,
        date_format=date_format,
        equality_attr=equality_attr
    )
    assert result == expected_result


get_invoice_period_ranges_data = [
    # case for February month first and end period dates are correctly prepared
    (
        arrow.get('2019-02-12').datetime,
        services.InvoicePeriod(
            period_start=arrow.get('2019-02-01').datetime,
            period_end=arrow.get('2019-02-28 23:59:59.999999').datetime,
        )
    ),
    # case when date is a first day of month
    (
        arrow.get('2019-02-01').datetime,
        services.InvoicePeriod(
            period_start=arrow.get('2019-02-01').datetime,
            period_end=arrow.get('2019-02-28 23:59:59.999999').datetime,
        )
    ),
    # case when date is a last day of month
    (
        arrow.get('2019-02-28').datetime,
        services.InvoicePeriod(
            period_start=arrow.get('2019-02-01').datetime,
            period_end=arrow.get('2019-02-28 23:59:59.999999').datetime,
        )
    ),
]


@pytest.mark.parametrize(
    'date,expected_result', get_invoice_period_ranges_data
)
def test_get_invoice_period_ranges(date, expected_result):
    """Test for `get_invoice_period_ranges` method."""
    result = services.get_invoice_period_ranges(date)
    assert result == expected_result


def test_get_invoice_for_matter_without_invoice(matter):
    """Test for `get_invoice_for_matter` method when matter has no invoice yet.

    When matter has no invoice yet for a desired period, there should be
    created a new invoice for it.

    """
    period_start = get_datetime_from_str('2018-02-04')
    period_end = get_datetime_from_str('2018-02-20')
    assert not matter.invoices.filter(
        period_start=period_start, period_end=period_end
    ).exists()

    invoice = services.get_invoice_for_matter(matter, period_start, period_end)
    assert matter.invoices.filter(
        period_start=period_start, period_end=period_end
    ).count() == 1
    assert invoice.period_start == period_start
    assert invoice.period_end == period_end


def test_get_invoice_for_matter_with_invoice_has_another_period(matter):
    """Test for `get_invoice_for_matter` method when matter has invoice.

    When matter has invoice with not corresponding period, there should be
    created a new invoice with another period for it.

    """
    period_start = get_datetime_from_str('2018-02-04')
    period_end = get_datetime_from_str('2018-02-20')
    factories.InvoiceFactory(
        matter=matter,
        period_start=period_start,
        period_end=period_end - timedelta(days=1)
    )

    new_invoice = services.get_invoice_for_matter(
        matter, period_start, period_end
    )
    assert matter.invoices.filter(
        period_start=period_start, period_end=period_end
    ).count() == 1
    assert new_invoice.period_start == period_start
    assert new_invoice.period_end == period_end


def test_get_invoice_for_matter_matter_has_invoice_w_same_period(matter):
    """Test for `get_invoice_for_matter` method when matter has invoice.

    When matter has invoice with the same period, there shouldn't be created
    any new invoice, the old invoice should be returned.

    """
    period_start = get_datetime_from_str('2018-02-04')
    period_end = get_datetime_from_str('2018-02-20')
    old_invoice = factories.InvoiceFactory(
        matter=matter,
        period_start=period_start,
        period_end=period_end
    )

    new_invoice = services.get_invoice_for_matter(
        matter, period_start, period_end
    )
    assert matter.invoices.filter(
        period_start=period_start, period_end=period_end
    ).count() == 1
    assert new_invoice == old_invoice


def test_send_invoice_to_recipients_success(monkeypatch, matter):
    """Test for `send_invoice_to_recipients` method when send is successful."""
    def mockreturn(self):
        return True
    monkeypatch.setattr(InvoiceEmailNotification, 'send', mockreturn)
    invoice = factories.InvoiceFactory(matter=matter)
    send_status = services.send_invoice_to_recipients(invoice, 'test@test.ru')
    assert send_status


def test_send_invoice_to_recipients_fail(monkeypatch, matter):
    """Test for `send_invoice_to_recipients` method when send is failed."""
    def mockreturn(self):
        return False
    monkeypatch.setattr(InvoiceEmailNotification, 'send', mockreturn)
    invoice = factories.InvoiceFactory(matter=matter)
    send_status = services.send_invoice_to_recipients(invoice, 'test@test.ru')
    assert not send_status


def test_prepare_invoice_for_payment(
    matter: models.Matter, attorney: AppUser
):
    """Test that prepare_invoice_for_payment cleans tb attachments."""
    period_start = arrow.utcnow().shift(years=100)
    period_end = period_start.shift(days=2)
    invoice: models.Invoice = factories.InvoiceFactory(
        period_start=period_start.datetime,
        period_end=period_end.datetime,
        matter=matter,
    )
    paid_invoice: models.Invoice = factories.InvoiceFactory(
        period_start=period_start.datetime,
        period_end=period_end.datetime,
        matter=matter
    )
    time_billings_count = 2
    time_billings = factories.BillingItemFactory.create_batch(
        matter=matter,
        created_by=attorney.user,
        date=period_start.shift(days=1).datetime,
        size=time_billings_count
    )
    # Check that two invoice have same tb attachments
    for time_billing in time_billings:
        assert time_billing in invoice.time_billing.all()
        assert time_billing in paid_invoice.time_billing.all()
    services.prepare_invoice_for_payment(paid_invoice)
    # Check that now only paid invoice has time billings and it's ones we
    # created
    for time_billing in time_billings:
        assert time_billing not in invoice.time_billing.all()
        assert time_billing in paid_invoice.time_billing.all()
    assert paid_invoice.time_billing.count() == time_billings_count


@pytest.mark.usefixtures('stripe_create_payment_intent')
def test_get_or_create_invoice_payment(matter: models.Matter):
    """Test that get_or_create_invoice_payment creates payment for invoice."""
    period_start = arrow.utcnow().shift(years=200)
    period_end = period_start.shift(days=2)
    invoice: models.Invoice = factories.InvoiceWithTBFactory(
        period_start=period_start.datetime,
        period_end=period_end.datetime,
        matter=matter,
        status=models.Invoice.INVOICE_STATUS_SENT,
    )
    payment = services.get_or_create_invoice_payment(invoice)
    # Check that payment was correctly created
    assert payment
    assert payment.status == Payment.STATUS_IN_PROGRESS
    assert payment.amount == invoice.fees_earned
    assert payment.recipient_id == matter.attorney_id
    assert payment.payer_id == matter.client_id
    application_fee_amount = (
        invoice.fees_earned * config.APPLICATION_FEE / 100
    )
    assert payment.application_fee_amount == application_fee_amount
