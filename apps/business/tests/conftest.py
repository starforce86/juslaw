import pytest

from ...users import models as user_models
from ...users.factories import AttorneyFactory, ClientFactory
from .. import factories, models


@pytest.fixture(scope='session')
def another_matter(django_db_blocker) -> models.Matter:
    """Create other matter."""
    with django_db_blocker.unblock():
        return factories.MatterFactory()


@pytest.fixture(scope='session')
def activities_matter(django_db_blocker) -> models.Matter:
    """Separate matter to check `activities` workflow."""
    with django_db_blocker.unblock():
        return factories.MatterFactory()


@pytest.fixture(scope='session')
def other_client(django_db_blocker) -> user_models.Client:
    """Create other client."""
    with django_db_blocker.unblock():
        return ClientFactory()


@pytest.fixture(scope='session')
def other_attorney(django_db_blocker) -> user_models.Attorney:
    """Create other attorney."""
    with django_db_blocker.unblock():
        return AttorneyFactory()


@pytest.fixture(scope='session')
def client_lead(
    django_db_blocker, client: user_models.Client
) -> models.Lead:
    """Create lead for client."""
    with django_db_blocker.unblock():
        return factories.LeadFactory(client=client, topic=None)


@pytest.fixture(scope='session')
def attorney_lead(
    django_db_blocker, attorney: user_models.Attorney
) -> models.Lead:
    """Create lead for attorney."""
    with django_db_blocker.unblock():
        return factories.LeadFactory(attorney=attorney, topic=None)


@pytest.fixture(scope='session')
def client_voice_consent(
    django_db_blocker, matter: models.Matter
) -> models.VoiceConsent:
    """Create test voice consent."""
    with django_db_blocker.unblock():
        return factories.VoiceConsentFactory(matter=matter)


@pytest.fixture(scope='session')
def other_voice_consent(django_db_blocker) -> models.VoiceConsent:
    """Create other test voice consent."""
    with django_db_blocker.unblock():
        return factories.VoiceConsentFactory()


@pytest.fixture(scope='session')
def other_video_call(
    django_db_blocker,
    other_attorney: user_models.Attorney,
    other_client: user_models.Client,
) -> models.VideoCall:
    """Create video call that was created for other client and attorney."""
    with django_db_blocker.unblock():
        video_call = models.VideoCall.objects.create()
        video_call.participants.add(other_attorney.pk, other_client.pk)
        return video_call


@pytest.fixture(scope='session')
def shared_matter(
    django_db_blocker, matter: models.Matter
) -> models.MatterSharedWith:
    """Create shared matter for testing."""
    with django_db_blocker.unblock():
        return factories.MatterSharedWithFactory(matter=matter)


@pytest.fixture(scope='session')
def open_invoice(
    django_db_blocker, matter: models.Matter
) -> models.Invoice:
    """Create pending invoice for testing."""
    with django_db_blocker.unblock():
        return factories.InvoiceWithTBFactory(
            matter=matter, status=models.Invoice.INVOICE_STATUS_OPEN
        )


@pytest.fixture(scope='session')
def sent_invoice(
    django_db_blocker, matter: models.Matter
) -> models.Invoice:
    """Create sent invoice for testing."""
    with django_db_blocker.unblock():
        return factories.InvoiceWithTBFactory(
            matter=matter, status=models.Invoice.INVOICE_STATUS_SENT
        )


@pytest.fixture(scope='session')
def to_be_paid_invoice(
    django_db_blocker, matter: models.Matter
) -> models.Invoice:
    """Create invoice which payment is in progress for testing."""
    with django_db_blocker.unblock():
        return factories.ToBePaidInvoice(matter=matter)


@pytest.fixture(scope='session')
def paid_invoice(
    django_db_blocker, matter: models.Matter
) -> models.Invoice:
    """Create paid invoice for testing."""
    with django_db_blocker.unblock():
        return factories.PaidInvoiceFactory(matter=matter)


@pytest.fixture(scope='session')
def other_invoice(django_db_blocker) -> models.Invoice:
    """Create invoice for testing."""
    with django_db_blocker.unblock():
        return factories.InvoiceFactory()


@pytest.fixture
def invoice(
    request,
    pending_invoice: models.Invoice,
    sent_invoice: models.Invoice,
    paid_invoice: models.Invoice,
    to_be_paid_invoice: models.Invoice,
    other_invoice: models.Invoice,
) -> models.Invoice:
    """Fixture to parametrize invoice fixtures."""
    mapping = {
        'pending_invoice': pending_invoice,
        'sent_invoice': sent_invoice,
        'paid_invoice': paid_invoice,
        'to_be_paid_invoice': to_be_paid_invoice,
        'other_invoice': other_invoice,
    }
    invoice = mapping[request.param]
    return invoice


@pytest.fixture(scope="session")
def not_paid_time_billing(
    django_db_blocker, matter: models.Matter, pending_invoice: models.Invoice
) -> models.BillingItem:
    """Create time billing for attorney."""
    with django_db_blocker.unblock():
        return factories.BillingItemFactory(
            matter=matter,
            date=pending_invoice.period_start
        )


@pytest.fixture(scope="session")
def to_be_paid_time_billing(
    django_db_blocker,
    matter: models.Matter,
    to_be_paid_invoice: models.Invoice
) -> models.BillingItem:
    """Create time billing(that will be paid) for attorney."""
    with django_db_blocker.unblock():
        return to_be_paid_invoice.time_billing.first()


@pytest.fixture(scope="session")
def paid_time_billing(
    django_db_blocker, matter: models.Matter, paid_invoice: models.Invoice
) -> models.BillingItem:
    """Get paid time billing for attorney."""
    with django_db_blocker.unblock():
        return paid_invoice.time_billing.first()


@pytest.fixture(scope="session")
def other_time_billing(django_db_blocker) -> models.BillingItem:
    """Create other time billing for testing."""
    with django_db_blocker.unblock():
        return factories.BillingItemFactory()


@pytest.fixture
def time_billing(
    request,
    to_be_paid_time_billing: models.BillingItem,
    not_paid_time_billing: models.BillingItem,
    paid_time_billing: models.BillingItem,
    other_time_billing: models.BillingItem,
) -> models.BillingItem:
    """Fixture to parametrize time_billing fixtures."""
    mapping = {
        'not_paid_time_billing': not_paid_time_billing,
        'paid_time_billing': paid_time_billing,
        'to_be_paid_time_billing': to_be_paid_time_billing,
        'other_time_billing': other_time_billing,
    }
    time_billing = mapping[request.param]
    return time_billing
