import pytest

from ...business.factories import LeadFactory, MatterFactory
from ...business.models import Lead, Matter
from .. import factories, models


@pytest.fixture(scope='module', autouse=True)
def matter(
    django_db_blocker,
    attorney: models.Attorney,
    client: models.Client,
    lead: Lead
) -> Matter:
    """Create matter for testing."""
    with django_db_blocker.unblock():
        return MatterFactory(
            client=client,
            attorney=attorney,
            status=Matter.STATUS_OPEN,
            lead=lead
        )


class TestAppUserManager:
    """Test AppUserManager for AppUser model."""

    def test_had_business_with_attorney(
        self,
        attorney: models.Attorney,
        client: models.Client,
        matter: Matter
    ):
        """Test had_business_with for attorney."""
        another_client = factories.ClientFactory(
            client_type=models.Client.FIRM_TYPE,
            organization_name='test'
        )
        client_by_invite = factories.InviteFactory(
            inviter_id=attorney.pk,
            user=another_client.user
        ).user_id
        client_by_lead = LeadFactory(
            attorney_id=attorney.pk, topic=None
        ).client_id
        client_matter = MatterFactory(attorney_id=attorney.pk).client_id

        clients = models.AppUser.objects.had_business_with(user=attorney.user)

        assert clients.exists()
        # Check that only clients returned
        assert not clients.exclude(attorney__isnull=True).exists()
        clients = clients.values_list('pk', flat=True)

        # This client had business by invite, matter and lead
        assert client.pk in clients
        # This client had business by invite
        assert client_by_invite in clients
        # This client had business by lead
        assert client_by_lead in clients
        # This client had business by matter
        assert client_matter in clients
        # This client hadn't business at all
        assert factories.AppUserWithClientFactory().pk not in clients

    def test_had_business_with_client(
        self,
        client: models.Client, attorney: models.Attorney,
        matter: Matter
    ):
        """"Test had_business_with for attorney."""
        attorney_by_invite = factories.InviteFactory(
            inviter=factories.AppUserWithAttorneyFactory(),
            user_id=client.user_id
        ).inviter_id
        attorney_by_lead = LeadFactory(client=client, topic=None).attorney_id
        attorney_matter = MatterFactory(client=client).attorney_id

        attorneys = models.AppUser.objects.had_business_with(
            user=client.user
        )

        assert attorneys.exists()
        # Check that only attorneys returned
        assert not attorneys.exclude(client__isnull=True).exists()
        attorneys = attorneys.values_list('pk', flat=True)

        # This attorney had business by invite, matter and lead
        assert attorney.pk in attorneys
        # This attorney had business by invite
        assert attorney_by_invite in attorneys
        # This attorney had business by lead
        assert attorney_by_lead in attorneys
        # This attorney had business by matter
        assert attorney_matter in attorneys
        # This attorney hadn't business at all
        assert factories.AppUserWithClientFactory().pk not in attorneys
