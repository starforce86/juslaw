from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

import pytest

from libs.docusign.constants import (
    ENVELOPE_STATUS_COMPLETED,
    ENVELOPE_STATUS_CREATED,
    ENVELOPE_STATUS_DECLINED,
    ENVELOPE_STATUS_DELIVERED,
    ENVELOPE_STATUS_SENT,
    ENVELOPE_STATUS_SIGNED,
    ENVELOPE_STATUS_VOIDED,
)

from apps.business.models import Matter

from ..factories import EnvelopeFactory
from ..models import Envelope


class TestEnvelopeModel:
    """Tests for `Envelope` model methods."""

    def test_db_initial_envelope_unique_constraint(self, envelope: Envelope):
        """Check `unique_initial_envelope_for_matter` DB constraint."""
        with pytest.raises(IntegrityError):
            EnvelopeFactory(matter=envelope.matter)

    @pytest.mark.parametrize(
        'envelope_type,is_initial', [
            (Envelope.TYPE_INITIAL, True),
            (Envelope.TYPE_EXTRA, False),
        ])
    def test_is_initial(
        self, envelope: Envelope, envelope_type: str, is_initial: bool
    ):
        """Check `is_initial` property works correctly."""
        envelope.type = envelope_type
        assert envelope.is_initial == is_initial

    @pytest.mark.parametrize(
        'envelope_status,is_created', [
            (ENVELOPE_STATUS_CREATED, True),
            (ENVELOPE_STATUS_COMPLETED, False),
        ])
    def test_is_created(
        self, envelope: Envelope, envelope_status: str, is_created: bool
    ):
        """Check `is_created` property works correctly."""
        envelope.status = envelope_status
        assert envelope.is_created == is_created

    def test_clean_type_no_duplicates_exists(self, envelope: Envelope):
        """Check `clean_type` method when envelope has no duplicates yet."""
        envelope.clean()

    def test_clean_type_not_duplicates(self, envelope: Envelope):
        """Check `clean_type` when matter has few not duplicated envelopes.
        """
        EnvelopeFactory(matter=envelope.matter, type=Envelope.TYPE_EXTRA)
        envelope.clean()

    def test_clean_type_duplicates(self, envelope: Envelope):
        """Check `clean_type` method when envelope has duplicates."""
        # make original envelope of another type to avoid issues with db
        # `integrity` error
        envelope.type = Envelope.TYPE_EXTRA
        envelope.save()

        EnvelopeFactory(matter=envelope.matter)
        # make it `initial` again to check test behavior
        envelope.type = Envelope.TYPE_INITIAL
        with pytest.raises(ValidationError):
            envelope.clean()

    @pytest.mark.parametrize(
        'transition,env_status_from,env_status_to,matter_status_from,'
        'matter_transition', [
            ('create', ENVELOPE_STATUS_SENT, ENVELOPE_STATUS_CREATED,
             Matter.STATUS_OPEN, 'open'),

            ('send', ENVELOPE_STATUS_CREATED, ENVELOPE_STATUS_SENT,
             Matter.STATUS_CLOSE, 'close'),

            ('decline', ENVELOPE_STATUS_SENT, ENVELOPE_STATUS_DECLINED,
             Matter.STATUS_CLOSE, 'close'),

            ('void', ENVELOPE_STATUS_SENT, ENVELOPE_STATUS_VOIDED,
             Matter.STATUS_CLOSE, 'close'),

            ('deliver', ENVELOPE_STATUS_SENT, ENVELOPE_STATUS_DELIVERED,
             None, None),

            ('sign', ENVELOPE_STATUS_SENT, ENVELOPE_STATUS_SIGNED, None, None),

            ('complete', ENVELOPE_STATUS_SENT, ENVELOPE_STATUS_COMPLETED,
             Matter.STATUS_CLOSE, 'close'),
        ]
    )
    def test_create_envelope_transition(
        self, envelope: Envelope, transition: str, env_status_from: str,
        env_status_to: str, matter_status_from: str, matter_transition: str,
        mocker
    ):
        """Test `create` envelope transition."""
        # change envelope status to a desired one for test
        envelope.status = env_status_from
        envelope.save()

        # change matter status to a desired one for test
        if matter_status_from:
            envelope.matter.status = matter_status_from
            envelope.matter.save()

        matter_updated_mock = mocker.patch(
            f'apps.business.models.matter.Matter.{matter_transition}'
        ) if matter_transition else None

        # call transition and check new `envelope` and `matter` statuses
        getattr(envelope, transition)()
        assert envelope.status == env_status_to
        if matter_updated_mock:
            matter_updated_mock.assert_called()
