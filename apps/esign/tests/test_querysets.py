import uuid
from datetime import timedelta

from django.test.utils import override_settings

from libs.docusign.constants import ENVELOPE_STATUS_SENT

from apps.business.models import Matter

from .. import factories
from ..models import Envelope, ESignProfile


class TestEnvelopeQuerySet:
    """Tests for `EnvelopeQuerySet` methods."""

    def test_available_for_user_by_attorney(
        self, envelope: Envelope, another_envelope: Envelope
    ):
        """Check `available_for_user` method.

        Check that attorney can get only envelopes for his own matters.

        """
        envelopes = Envelope.objects.all().available_for_user(
            envelope.matter.attorney.user
        )
        assert not envelopes.filter(id=another_envelope.id).exists()

    def test_available_for_user_by_client(
        self, envelope: Envelope, another_envelope: Envelope
    ):
        """Check `available_for_user` method.

        Check that client can't get any available envelopes.

        """
        envelopes = Envelope.objects.all().available_for_user(
            envelope.matter.client.user
        )
        assert not envelopes.exists()

    def test_old_envelopes_for_not_production(self, matter: Matter):
        """Check `old_envelopes` method for not production env.


        | Envelope |    Created   | Should be returned
        |----------|--------------|-------------------
        |   env_1  |  29 days ago | +
        |----------|--------------|-------------------
        |   env_2  |  40 days ago | +
        |----------|--------------|-------------------
        |   env_3  |  20 days ago | -

        """
        env_1, env_2, env_3 = factories.EnvelopeFactory.create_batch(
            matter=matter, type=Envelope.TYPE_EXTRA, size=3
        )
        env_1.created = env_1.created - timedelta(days=29)
        env_1.save()

        env_2.created = env_2.created - timedelta(days=40)
        env_2.save()

        env_3.created = env_3.created - timedelta(days=20)
        env_3.save()

        envelopes = Envelope.objects.all().old_envelopes()
        assert envelopes.filter(id__in=[env_1.id, env_2.id]).exists()
        assert not envelopes.filter(id=env_3.id).exists()

    @override_settings(ENVIRONMENT='production')
    def test_old_envelopes_for_production(self, matter: Matter):
        """Check `old_envelopes` method for not production env.

        | Envelope |    Created   |  Status  | Should be returned
        |----------|--------------|----------|-------------------
        |   env_1  |  29 days ago |  Created | +
        |----------|--------------|----------|-------------------
        |   env_2  |  40 days ago |  Created | +
        |----------|--------------|----------|-------------------
        |   env_3  |  40 days ago |   Sent   | -
        |----------|--------------|----------|-------------------
        |   env_4  |  20 days ago | Created  | -

        """
        env_1, env_2, env_3, env_4 = factories.EnvelopeFactory.create_batch(
            matter=matter, type=Envelope.TYPE_EXTRA, size=4
        )
        env_1.created = env_1.created - timedelta(days=29)
        env_1.save()

        env_2.created = env_2.created - timedelta(days=40)
        env_2.save()

        env_3.created = env_3.created - timedelta(days=40)
        env_3.status = ENVELOPE_STATUS_SENT
        env_3.save()

        env_4.created = env_4.created - timedelta(days=20)
        env_4.save()

        envelopes = Envelope.objects.all().old_envelopes()
        assert envelopes.filter(id__in=[env_1.id, env_2.id]).exists()
        assert not envelopes.filter(id__in=[env_3.id, env_4.id]).exists()


class TestESignProfileQuerySet:
    """Tests for `ESignProfileQuerySet` methods."""

    def test_get_profile_by_consent_id(
        self, esign_profile: ESignProfile, another_esign_profile: ESignProfile
    ):
        """Check `get_profile_by_consent_id` method when consent exists.

        Check that only one esign profile with corresponding `consent_id` is
        returned.

        """
        profile = ESignProfile.objects.all().get_profile_by_consent_id(
            esign_profile.consent_id
        )
        assert profile == esign_profile

    def test_get_profile_by_consent_id_no_profile_found(
        self, esign_profile: ESignProfile, another_esign_profile: ESignProfile
    ):
        """Check `get_profile_by_consent_id` method when no consent exists."""
        profile = ESignProfile.objects.all().get_profile_by_consent_id(
            uuid.uuid4()
        )
        assert profile is None
