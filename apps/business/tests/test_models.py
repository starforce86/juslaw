from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError

import pytest
from stripe import PaymentIntent

from ...finance.models import Payment
from .. import factories, models


class TestMatterModel:
    """Tests for `Matter` model methods."""

    def test_clean_code_duplicate_for_one_attorney(
        self, matter, another_matter
    ):
        """Check `clean_code` matter method.

        Error should be raised if matter's codes are not unique for one
        attorney.

        """
        another_matter.code = matter.code
        another_matter.attorney = matter.attorney
        with pytest.raises(ValidationError):
            another_matter.clean_code()

        another_matter.refresh_from_db()

    def test_clean_code_duplicate_for_different_attorneys(
        self, matter, another_matter
    ):
        """Check `clean_code` matter method.

        Error shouldn't be raised if codes are repeated for different
        attorneys.

        """
        another_matter.refresh_from_db()
        another_matter.code = matter.code
        another_matter.clean_code()

    def test_clean_code_not_duplicate_for_one_attorney(
        self, matter, another_matter
    ):
        """Check `clean_code` matter method.

        Error shouldn't be raised if codes are different for one attorney.

        """
        another_matter.refresh_from_db()
        another_matter.attorney = matter.attorney
        another_matter.clean_code()

    def test_is_shared_for_user(self, matter, another_matter):
        """Test `is_shared_for_user` matter method."""
        user = factories.MatterSharedWithFactory(matter=matter).user
        assert matter.is_shared_for_user(user)
        assert not another_matter.is_shared_for_user(user)


class TestBillingItemAttachmentModel:
    """Tests for `BillingItemAttachment` model methods."""

    def test_clean_invoice_for_matters(
        self, matter, another_matter
    ):
        """Check `clean_invoice` method by matters.

        It's not allowed to create attachments for different matters.

        """
        tba = factories.BillingItemAttachmentFactory(
            time_billing=factories.BillingItemFactory(matter=matter),
            invoice=factories.InvoiceFactory(matter=another_matter),
        )
        with pytest.raises(ValidationError):
            tba.clean_invoice()

    def test_clean_invoice_not_hourly_rated_matter(self):
        """Check `clean_invoice` method for not hourly rated matters."""
        matter = factories.MatterFactory(
            rate_type=models.Matter.RATE_TYPE_FIXED
        )
        tba = factories.BillingItemAttachmentFactory(
            time_billing=factories.BillingItemFactory(matter=matter),
            invoice=factories.InvoiceFactory(matter=matter),
        )
        with pytest.raises(ValidationError):
            tba.clean_invoice()

    def test_clean_invoice_time_billing_within_period(self, matter):
        """Check `clean_invoice` method for time billing out of invoice period.
        """
        tba = factories.BillingItemAttachmentFactory(
            time_billing=factories.BillingItemFactory(
                matter=matter,
                date=datetime.now() - timedelta(60)
            ),
            invoice=factories.InvoiceFactory(
                matter=matter,
                period_start=datetime.now(),
                period_end=datetime.now() + timedelta(days=1),
            )
        )
        with pytest.raises(ValidationError):
            tba.clean_invoice()


class TestVoiceConsentModel:
    """Test `VoiceConsent` model."""

    def test_clean_file(
        self, client_voice_consent: models.VoiceConsent, image_file
    ):
        """Check that validation error'll be raised on non audio file."""
        client_voice_consent.file = image_file

        with pytest.raises(ValidationError):
            client_voice_consent.clean()

        client_voice_consent.refresh_from_db()

    def test_title_matter_constraint(self, client_voice_consent):
        """Test that we can't create consent with same title in one matter."""
        with pytest.raises(IntegrityError):
            factories.VoiceConsentFactory(
                matter_id=client_voice_consent.matter_id,
                title=client_voice_consent.title,
            )


class TestInvoiceModel:
    """Test invoice model."""

    @pytest.mark.usefixtures('stripe_create_payment_intent')
    def test_start_payment_process(self, matter: models.Matter):
        """Check start_payment_process transition."""
        sent_invoice: models.Invoice = factories.InvoiceWithTBFactory(
            matter=matter, status=models.Invoice.INVOICE_STATUS_SENT
        )
        payment = sent_invoice.start_payment_process()
        assert payment
        assert payment.status == Payment.STATUS_IN_PROGRESS
        assert (
            sent_invoice.payment_status ==
            models.Invoice.PAYMENT_STATUS_IN_PROGRESS
        )

    def test_finalize_payment(self, matter: models.Matter, mocker):
        notification_mock = mocker.patch(
            'apps.business.notifications.InvoicePaymentSucceededNotification',
        )
        to_be_paid_invoice: models.Invoice = factories.ToBePaidInvoice(
            matter=matter,
        )
        to_be_paid_invoice.finalize_payment()

        # check notification was called twice - for client and for attorney
        notification_mock.assert_has_calls([
            mocker.call(
                paid_object=to_be_paid_invoice, recipient=matter.client.user
            )
        ])
        notification_mock.assert_has_calls([
            mocker.call(
                paid_object=to_be_paid_invoice, recipient=matter.attorney.user
            )
        ])
        assert notification_mock.call_count == 2
        assert (
            to_be_paid_invoice.payment_status ==
            models.Invoice.PAYMENT_STATUS_PAID
        )

    def test_fail_payment(self, matter: models.Matter, mocker):
        notification_mock = mocker.patch(
            'apps.business.notifications.InvoicePaymentFailedNotification',
        )
        to_be_paid_invoice: models.Invoice = factories.ToBePaidInvoice(
            matter=matter,
        )
        to_be_paid_invoice.fail_payment()
        notification_mock.assert_called()
        assert (
            to_be_paid_invoice.payment_status ==
            models.Invoice.PAYMENT_STATUS_FAILED
        )

    def test_cancel_payment(self, matter: models.Matter, mocker):
        notification_mock = mocker.patch(
            'apps.business.notifications.InvoicePaymentCanceledNotification',
        )
        mocker.patch(
            'stripe.PaymentIntent.retrieve',
            return_value=PaymentIntent()
        )
        mocker.patch(
            'stripe.PaymentIntent.cancel',
            return_value=PaymentIntent()
        )
        to_be_paid_invoice: models.Invoice = factories.ToBePaidInvoice(
            matter=matter,
        )
        to_be_paid_invoice.cancel_payment()
        notification_mock.assert_called()
        assert (
            to_be_paid_invoice.payment_status ==
            models.Invoice.PAYMENT_STATUS_NOT_STARTED
        )
