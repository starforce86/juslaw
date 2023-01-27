import pytest

from apps.business.factories import (
    BillingItemAttachmentFactory,
    InvoiceFactory,
)
from apps.business.models import Invoice, Matter


@pytest.fixture(scope='session')
def invoice_no_time_billing(django_db_blocker, matter: Matter) -> Invoice:
    """Create invoice for testing."""
    with django_db_blocker.unblock():
        return InvoiceFactory(matter=matter)


@pytest.fixture(scope='session')
def invoice_with_time_billing(django_db_blocker, matter: Matter) -> Invoice:
    """Create invoice for testing."""
    with django_db_blocker.unblock():
        invoice = InvoiceFactory(matter=matter)
        BillingItemAttachmentFactory.create_batch(size=2, invoice=invoice)
        return invoice


@pytest.fixture
def invoice(
    request, invoice_no_time_billing, invoice_with_time_billing
) -> Invoice:
    """Fixture to use fixtures in decorator parametrize for invoice object."""
    mapping = {
        'invoice_no_time_billing': invoice_no_time_billing,
        'invoice_with_time_billing': invoice_with_time_billing,
    }
    return mapping.get(request.param)
