from datetime import datetime, timedelta

from django.db.utils import IntegrityError

import arrow
import pytest

from apps.users.models import AppUser

from ... import factories, models


@pytest.fixture(scope='module')
def invoice(
    django_db_blocker, matter: models.Matter
) -> models.Invoice:
    """Create invoice for testing."""
    with django_db_blocker.unblock():
        return factories.InvoiceFactory(matter=matter)


def test_calculate_fees_hourly_rated_matter(matter):
    """Test that `calculate_fees` signal works correctly."""
    tb = factories.BillingItemFactory(matter=matter, fees=0)
    assert tb.fees != 0


def test_calculate_fees_not_hourly_rated_matter():
    """Test that `calculate_fees` signal works correctly."""
    matter = factories.MatterFactory(
        rate_type=models.Matter.RATE_TYPE_ALTERNATIVE
    )
    tb = factories.BillingItemFactory(matter=matter, fees=0)
    assert tb.fees == 0


def test_process_invoice_create_update_not_hourly_rated():
    """Check workflow of invoice create, update `process_invoice_create_update`

    When invoice is related to not `hourly` rated matter -> no reattachments
    should be made.

    """
    invoice = factories.InvoiceFactory(
        matter__rate_type=models.Matter.RATE_TYPE_ALTERNATIVE
    )
    tb = factories.BillingItemFactory(
        date=invoice.period_start, matter=invoice.matter
    )
    tb.attached_invoice.all().delete()

    # check that time billing is not attached when invoice's matter is not
    # hourly rated on update
    invoice.period_end = invoice.period_start + timedelta(days=4)
    invoice.save()
    assert not tb.invoices.exists()

    # check that time billing is not attached when invoice's matter is not
    # hourly rated on create
    factories.InvoiceFactory(
        matter=invoice.matter,
        period_start=invoice.period_start,
        period_end=invoice.period_end,
    )
    assert not tb.invoices.exists()


def test_process_invoice_create_update_check_update(invoice):
    """Check workflow of invoice update `process_invoice_create_update`

    If invoice `date` is not changed -> no time billings reattachments should
    be done. Otherwise matched time billing should be attached to invoice.

    """
    tb = factories.BillingItemFactory(
        date=invoice.period_start, matter=invoice.matter
    )
    another_matter_tb = factories.BillingItemFactory(
        date=invoice.period_start
    )
    tb.attached_invoice.all().delete()
    another_matter_tb.attached_invoice.all().delete()

    # check that after invoice `title` field update tb wasn't reattached
    invoice.title = 'Test'
    invoice.save()
    assert not tb.invoices.exists()
    assert not another_matter_tb.invoices.exists()

    # check that after invoice `period_end` field update tb was reattached
    invoice.period_end = invoice.period_start + timedelta(days=4)
    invoice.save()
    assert tb.invoices.count() == 1
    assert tb.invoices.first() == invoice
    # invoice is not attached to another matters time billings
    assert another_matter_tb.invoices.count() == 0


def test_process_invoice_create_update_check_create(matter):
    """Check workflow of invoice create `process_invoice_create_update`

    If new invoice is created - all matched time billings should be attached
    to it.

    """
    tb = factories.BillingItemFactory(matter=matter)
    another_matter_tb = factories.BillingItemFactory(date=tb.date)
    tb.attached_invoice.all().delete()
    another_matter_tb.attached_invoice.all().delete()

    # check that after invoice creation only related to this matter time
    # billings are attached
    invoice = factories.InvoiceFactory(
        matter=matter,
        period_start=tb.date,
        period_end=tb.date + timedelta(days=1)
    )
    assert tb.invoices.count() == 1
    assert tb.invoices.first() == invoice
    # check that another matter invoice is not reattached
    assert another_matter_tb.invoices.count() == 0


def test_process_invoice_create_update_few_matched_time_billings(matter):
    """Check time billing update `process_time_billing_create_update`.

    Check that when time billing is for past periods and it's already
    attached to few invoices - it would be correctly updated.

    1. Invoice 1 - 58 -> 59 (new invoice, to add)
    2. Invoice 2 - 57 -> 58 (old invoice, to delete)
    3. Invoice 3 - 58 -> 59 (old invoice, to ignore)

    """
    invoice = factories.InvoiceFactory(
        matter=matter,
        period_start=(datetime.now() - timedelta(days=35)),
        period_end=(datetime.now() - timedelta(days=30)),
    )
    to_add = factories.BillingItemFactory(
        matter=matter,
        date=datetime.now() - timedelta(days=25),
    )
    to_delete = factories.BillingItemFactory(
        matter=matter,
        date=datetime.now() - timedelta(days=32),
    )
    to_ignore = factories.BillingItemFactory(
        matter=matter,
        date=datetime.now() - timedelta(days=30),
    )

    # check that after invoice period update tb were correctly reattached
    assert invoice.attached_time_billing.count() == 2
    assert invoice.attached_time_billing.filter(
        time_billing__id__in=[to_delete.id, to_ignore.id]
    ).count() == 2

    # check that after time billing update invoice will be added again
    invoice.period_start = datetime.now() - timedelta(days=30)
    invoice.period_end = datetime.now() - timedelta(days=20)
    invoice.save()
    assert invoice.attached_time_billing.count() == 2
    assert invoice.attached_time_billing.filter(
        time_billing__id__in=[to_add.id, to_ignore.id]
    ).count() == 2


def test_process_time_billing_create_update_not_hourly_rated():
    """Check `process_time_billing_create_update` for not `hourly` rated matter

    When time billing is related to not `hourly` rated matter -> no invoices
    should be generated for it.

    """
    tb = factories.BillingItemFactory(
        matter__rate_type=models.Matter.RATE_TYPE_ALTERNATIVE,
        date=datetime.now() - timedelta(days=60)
    )
    assert not tb.invoices.exists()


def test_process_time_billing_create_update_not_date_updated(matter):
    """Check `process_time_billing_create_update` when not `date` updated

    When time billing not `date` field is updated - no invoices reattachments
    should be made.

    """
    tb = factories.BillingItemFactory(
        matter=matter,
        date=datetime.now() - timedelta(days=60)
    )
    assert tb.attached_invoice.count() == 1

    # check that no invoices appears after time billing `date` update
    tb.attached_invoice.all().delete()
    tb.description = 'Test'
    tb.save()
    assert not tb.invoices.exists()


def test_process_time_billing_create_update_check_current_period_no_invoice(
    matter
):
    """Check `process_time_billing_create_update`

    Check if time billing has no matching invoice in DB - no new invoice would
    be added (cause system assumes that invoice would be generated on the
    beginning of a next month automatically by celery).

    """
    # check that after time billing create tb wasn't attached to invoice
    tb = factories.BillingItemFactory(date=datetime.now())
    assert not tb.invoices.exists()

    # check that after time billing `date` update not matched anymore invoices
    # are deleted
    tb = factories.BillingItemFactory(date=datetime.now() - timedelta(days=35))
    assert tb.invoices.count() == 1
    tb.date = datetime.now()
    tb.save()
    assert tb.invoices.count() == 0


def test_process_time_billing_create_update_check_current_period_with_invoice(
    matter
):
    """Check `process_time_billing_create_update`

    If for current period there is already existing `invoice` -> time
    billing should be reattached to it.

    """
    invoice = factories.InvoiceFactory(
        period_start=datetime.now(),
        period_end=datetime.now() + timedelta(days=2)
    )
    # check that after time billing create tb wasn't attached to invoice
    tb = factories.BillingItemFactory(
        matter=invoice.matter,
        date=datetime.now()
    )

    # check that after time billing update invoice will be added
    assert tb.invoices.count() == 1
    assert tb.invoices.first() == invoice


def test_process_time_billing_create_update_check_past_period_no_invoice(
    matter
):
    """Check `process_time_billing_create_update`

    Check that when time billing is in past period without matching invoices
    -> new invoice will be generated.

    """
    # check that after billing item create tb wasn't attached to invoice
    tb = factories.BillingItemFactory(
        matter=matter,
        date=datetime.now() - timedelta(days=60)
    )

    # check that after billing item update invoice will be added again
    assert tb.invoices.count() == 1


def test_process_time_billing_create_update_few_matched_invoices(matter):
    """Check time billing update `process_time_billing_create_update`.

    Check that when time billing is for past periods and it's already
    attached to few invoices - it would be correctly updated.

    1. Invoice 1 - 58 -> 59 (new invoice, to add)
    2. Invoice 2 - 57 -> 58 (old invoice, to delete)
    3. Invoice 3 - 58 -> 59 (old invoice, to ignore)

    """
    to_add = factories.InvoiceFactory(
        matter=matter,
        period_start=datetime.now() - timedelta(days=59),
        period_end=datetime.now() - timedelta(days=58),
    )
    # to delete
    factories.InvoiceFactory(
        matter=matter,
        period_start=datetime.now() - timedelta(days=58),
        period_end=datetime.now() - timedelta(days=57),
    )
    to_ignore = factories.InvoiceFactory(
        matter=matter,
        period_start=datetime.now() - timedelta(days=59),
        period_end=datetime.now() - timedelta(days=58),
    )

    # check that after billing item create tb wasn't attached to invoice
    tb = factories.BillingItemFactory(
        matter=matter,
        date=datetime.now() - timedelta(days=58)
    )

    # delete attachment for `to_add` invoice
    models.BillingItemAttachment.objects.filter(
        invoice=to_add, time_billing=tb
    ).delete()

    # check that after time billing update invoice will be added again
    tb.date = datetime.now() - timedelta(days=59)
    tb.save()
    assert tb.invoices.count() == 2
    assert set(tb.invoices.values_list('id', flat=True)) == \
           set([to_add.id, to_ignore.id])


def test_set_created_by_for_time_billing_update():
    """Test `set_created_by` signal on time billing update."""
    tb = factories.BillingItemFactory()

    # `created_by` field is not set on update
    with pytest.raises(IntegrityError):
        tb.id = None
        tb.created_by = None
        tb.save()


def test_set_created_by_for_time_billing_create():
    """Test `set_created_by` signal on time billing create."""
    tb = factories.BillingItemFactory(created_by=None)
    assert tb.created_by == tb.matter.attorney.user


def test_attach_tb_to_paid_or_to_be_paid_invoice(
    matter: models.Matter, attorney: AppUser
):
    """Test that new tb won't be attached to paid or to be paid invoice."""
    period_start = arrow.utcnow()
    period_end = period_start.shift(days=2)
    factory_params = dict(
        period_start=period_start.datetime,
        period_end=period_end.datetime,
        matter=matter,
    )
    paid_invoice: models.Invoice = factories.PaidInvoiceFactory(
        **factory_params
    )
    to_be_paid_invoice: models.Invoice = factories.ToBePaidInvoice(
        **factory_params
    )
    time_billing = factories.BillingItemFactory(
        matter=matter,
        created_by=attorney.user,
        date=period_start.shift(days=1).datetime,
    )
    assert time_billing not in to_be_paid_invoice.time_billing.all()
    assert time_billing not in paid_invoice.time_billing.all()


def test_attach_invoice_to_paid_or_to_be_paid_tb(matter: models.Matter):
    """Test that new invoice won't be attached to paid or to be paid tb."""
    period_start = arrow.utcnow()
    period_end = period_start.shift(days=2)
    factory_params = dict(
        period_start=period_start.datetime,
        period_end=period_end.datetime,
        matter=matter,
    )
    paid_invoice: models.Invoice = factories.PaidInvoiceFactory(
        **factory_params
    )
    to_be_paid_invoice: models.Invoice = factories.ToBePaidInvoice(
        **factory_params
    )
    new_invoice: models.Invoice = factories.InvoiceFactory(
        **factory_params
    )
    # Check that paid or to be paid tb got attached to new invoice
    for time_billing in paid_invoice.time_billing.all():
        assert time_billing not in new_invoice.time_billing.all()
    for time_billing in to_be_paid_invoice.time_billing.all():
        assert time_billing not in new_invoice.time_billing.all()
