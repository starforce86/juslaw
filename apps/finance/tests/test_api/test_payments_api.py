from typing import Union

from django.db import IntegrityError
from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest
from djstripe.enums import PaymentIntentStatus
from stripe import PaymentIntent

from libs.testing.constants import FORBIDDEN, OK

from ....business.factories import (
    InvoiceFactory,
    InvoiceWithTBFactory,
    MatterFactory,
    MatterSharedWithFactory,
    PaidInvoiceFactory,
    ToBePaidInvoice,
)
from ....business.models import Invoice, Matter
from ....users.factories import (
    AttorneyFactory,
    ClientFactory,
    PaidSupportFactory,
    SupportFactory,
    SupportVerifiedFactory,
    SupportVerifiedWithPaymentFactory,
)
from ....users.models import AppUser, Attorney, Client, Support
from ... import factories, models


def get_start_payment_url():
    """Get url to start payment."""
    return reverse_lazy(
        'v1:payments-start-payment-process',
    )


def get_cancel_payment(payment: models.Payment):
    """Get url for payment cancellation."""
    return reverse_lazy(
        'v1:payments-cancel', kwargs={'pk': payment.pk}
    )


@pytest.fixture(scope='module')
def client(django_db_blocker) -> Client:
    """Create client for testing."""
    with django_db_blocker.unblock():
        return ClientFactory()


@pytest.fixture(scope='module')
def attorney(django_db_blocker) -> Attorney:
    """Create attorney for testing."""
    with django_db_blocker.unblock():
        attorney: Attorney = AttorneyFactory()
        # Generate finance profile
        factories.FinanceProfileFactoryWithVerifiedAccount(user=attorney.user)
        return attorney


@pytest.fixture(scope='module')
def shared_attorney(django_db_blocker, matter: Matter) -> Attorney:
    """Create attorney for testing."""
    with django_db_blocker.unblock():
        attorney = AttorneyFactory()
        try:
            MatterSharedWithFactory(matter=matter, user=attorney.user)
        except IntegrityError:
            pass
        return attorney


@pytest.fixture(scope='module')
def not_verified_support(django_db_blocker) -> Support:
    """Create not verified support for users app testing."""
    with django_db_blocker.unblock():
        return SupportFactory()


@pytest.fixture(scope='module')
def support(django_db_blocker) -> Support:
    """Create support for users app testing."""
    with django_db_blocker.unblock():
        return SupportVerifiedFactory()


@pytest.fixture(scope='module')
def support_with_payment_in_progress(django_db_blocker) -> Support:
    """Create support with paid fee for users app testing."""
    with django_db_blocker.unblock():
        return SupportVerifiedWithPaymentFactory()


@pytest.fixture(scope='module')
def paid_support(django_db_blocker) -> Support:
    """Create support with paid fee for users app testing."""
    with django_db_blocker.unblock():
        return PaidSupportFactory()


@pytest.fixture
def user(
    request,
    client: Client,
    attorney: Attorney,
    not_verified_support: Support,
    support: Support,
    support_with_payment_in_progress: Support,
    paid_support: Support,
    other_client: Client,
    other_attorney: Attorney,
    other_support: Support,
    shared_attorney: Attorney,
) -> Union[AppUser, None]:
    """Fixture to use fixtures in decorator parametrize for AppUser object."""
    mapping = {
        'anonymous': None,
        'client': client,
        'attorney': attorney,
        'not_verified_support': not_verified_support,
        'support': support,
        'support_with_payment_in_progress': support_with_payment_in_progress,
        'paid_support': paid_support,
        'other_client': other_client,
        'other_attorney': other_attorney,
        'other_support': other_support,
        'shared_attorney': shared_attorney,
    }
    param_user = mapping.get(request.param)
    if param_user is None:
        return param_user
    return param_user.user


@pytest.fixture(scope='module')
def matter(
    django_db_blocker, attorney: Attorney, client: Client
) -> Matter:
    """Create matter for testing."""
    with django_db_blocker.unblock():
        return MatterFactory(
            attorney=attorney,
            client=client,
        )


@pytest.fixture(scope='module')
def open_invoice(
    django_db_blocker, matter: Matter
) -> Invoice:
    """Create pending invoice for testing."""
    with django_db_blocker.unblock():
        return InvoiceWithTBFactory(
            matter=matter, status=Invoice.INVOICE_STATUS_OPEN
        )


@pytest.fixture(scope='module')
def sent_invoice(
    django_db_blocker, matter: Matter
) -> Invoice:
    """Create sent invoice for testing."""
    with django_db_blocker.unblock():
        return InvoiceWithTBFactory(
            matter=matter, status=Invoice.INVOICE_STATUS_SENT
        )


@pytest.fixture(scope='module')
def to_be_paid_invoice(
    django_db_blocker, matter: Matter
) -> Invoice:
    """Create invoice which payment is in progress for testing."""
    with django_db_blocker.unblock():
        return ToBePaidInvoice(matter=matter)


@pytest.fixture(scope='module')
def paid_invoice(
    django_db_blocker, matter: Matter
) -> Invoice:
    """Create paid invoice for testing."""
    with django_db_blocker.unblock():
        return PaidInvoiceFactory(matter=matter)


@pytest.fixture(scope='module')
def other_invoice(django_db_blocker) -> Invoice:
    """Create invoice for testing."""
    with django_db_blocker.unblock():
        return InvoiceFactory()


@pytest.fixture(scope='module')
def other_sent_invoice(
    django_db_blocker, other_invoice: Invoice
) -> Invoice:
    """Create sent invoice for testing."""
    with django_db_blocker.unblock():
        return InvoiceWithTBFactory(
            matter_id=other_invoice.matter_id,
            status=Invoice.INVOICE_STATUS_SENT
        )


@pytest.fixture(scope='module')
def other_to_be_paid_invoice(
    django_db_blocker, other_invoice: Invoice
) -> Invoice:
    """Create to be paid invoice for testing."""
    with django_db_blocker.unblock():
        return ToBePaidInvoice(matter_id=other_invoice.matter_id)


@pytest.fixture
def can_be_paid_object(
    request,
    pending_invoice: Invoice,
    sent_invoice: Invoice,
    paid_invoice: Invoice,
    to_be_paid_invoice: Invoice,
    other_invoice: Invoice,
    other_sent_invoice: Invoice,
    other_to_be_paid_invoice: Invoice,
    not_verified_support: Support,
    support: Support,
    support_with_payment_in_progress: Support,
    paid_support: Support,
) -> Union[Invoice, Support]:
    """Fixture to parametrize objects that can be paid."""
    mapping = {
        'pending_invoice': pending_invoice,
        'sent_invoice': sent_invoice,
        'paid_invoice': paid_invoice,
        'to_be_paid_invoice': to_be_paid_invoice,
        'other_invoice': other_invoice,
        'other_sent_invoice': other_sent_invoice,
        'other_to_be_paid_invoice': other_to_be_paid_invoice,
        'not_verified_support': not_verified_support,
        'support': support,
        'support_with_payment_in_progress': support_with_payment_in_progress,
        'paid_support': paid_support,
    }
    invoice = mapping[request.param]
    return invoice


class TestAuthUserAPI:
    """Test payments api for authenticated users.

    All users have access to it.
    Only clients can pay for invoices.

    """

    @pytest.mark.usefixtures('stripe_create_payment_intent')
    @pytest.mark.parametrize(
        argnames='user, can_be_paid_object, status_code',
        argvalues=(
            ('client', 'pending_invoice', FORBIDDEN),
            ('client', 'sent_invoice', OK),
            ('client', 'to_be_paid_invoice', OK),
            ('client', 'paid_invoice', FORBIDDEN),
            # Check that client can't pay for foreign invoices
            ('client', 'other_invoice', FORBIDDEN),
            ('client', 'other_sent_invoice', FORBIDDEN),
            ('client', 'other_to_be_paid_invoice', FORBIDDEN),
            ('attorney', 'pending_invoice', FORBIDDEN),
            ('attorney', 'sent_invoice', FORBIDDEN),
            ('attorney', 'paid_invoice', FORBIDDEN),
            ('attorney', 'to_be_paid_invoice', FORBIDDEN),
            # Check that attorney can't access to foreign invoices
            ('attorney', 'other_invoice', FORBIDDEN),
            # Check attorney and client can't pay for support
            ('client', 'support', FORBIDDEN),
            ('attorney', 'support', FORBIDDEN),
            # Check Non-verified support can't pay fee
            ('not_verified_support', 'not_verified_support', FORBIDDEN),
            # Check verified support can pay fee
            ('support', 'support', OK),
            (
                'support_with_payment_in_progress',
                'support_with_payment_in_progress',
                OK
            ),
            # Check support can't pay fee twice
            ('paid_support', 'paid_support', FORBIDDEN),
        ),
        indirect=True
    )
    def test_get_payment_intent(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code: int,
        can_be_paid_object: Union[Invoice, Support],
    ):
        """Check that client can get payment intent for invoice."""
        api_client.force_authenticate(user=user)
        response = api_client.post(
            get_start_payment_url(),
            data=dict(
                object_type=can_be_paid_object.model_name,
                object_id=can_be_paid_object.pk,
            )
        )
        assert response.status_code == status_code, response.data
        if status_code != OK:
            return

        can_be_paid_object.refresh_from_db()
        # Check that status was changed and payment is in correct status
        assert (
            can_be_paid_object.payment_status ==
            models.AbstractPaidObject.PAYMENT_STATUS_IN_PROGRESS
        )
        payment = can_be_paid_object.payment
        assert payment
        assert payment.status == models.Payment.STATUS_IN_PROGRESS

    @pytest.mark.parametrize(
        argnames='user, can_be_paid_object, status_code',
        argvalues=(
            ('client', 'to_be_paid_invoice', OK),
            ('client', 'paid_invoice', FORBIDDEN),
            ('client', 'other_to_be_paid_invoice', FORBIDDEN),
            ('attorney', 'paid_invoice', FORBIDDEN),
            ('attorney', 'to_be_paid_invoice', FORBIDDEN),
            ('attorney', 'other_to_be_paid_invoice', FORBIDDEN),
            # Check attorney and client can't cancel support payment
            ('client', 'support_with_payment_in_progress', FORBIDDEN),
            ('attorney', 'support_with_payment_in_progress', FORBIDDEN),
            # Check support can't cancel payment fee of other support
            ('support', 'support_with_payment_in_progress', FORBIDDEN),
            # Check support can cancel payment fee
            (
                'support_with_payment_in_progress',
                'support_with_payment_in_progress',
                OK
            ),
            # Check support can't cancel payment once it paid
            ('paid_support', 'paid_support', FORBIDDEN),
        ),
        indirect=True
    )
    def test_cancel_payment(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code: int,
        can_be_paid_object: Union[Invoice],
        mocker
    ):
        """Check that client can cancel payment intent for invoice."""
        payment_intent = PaymentIntent()
        payment_intent['status'] = PaymentIntentStatus.requires_payment_method
        mocker.patch(
            'stripe.PaymentIntent.retrieve',
            return_value=payment_intent
        )
        mocker.patch(
            'stripe.PaymentIntent.cancel',
            return_value=PaymentIntent()
        )
        api_client.force_authenticate(user=user)
        can_be_paid_object.refresh_from_db()
        payment = can_be_paid_object.payment
        response = api_client.post(get_cancel_payment(payment))

        assert response.status_code == status_code, response.data
        if status_code != OK:
            return

        can_be_paid_object.refresh_from_db()
        assert (
            can_be_paid_object.payment_status ==
            models.AbstractPaidObject.PAYMENT_STATUS_NOT_STARTED
        )
        assert not can_be_paid_object.payment
        payment.refresh_from_db()
        assert payment.status == models.Payment.STATUS_CANCELED
