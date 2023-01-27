from datetime import datetime

from django.contrib.gis.geos import Point

import arrow
import pytest

from ...business.factories import (
    LeadFactory,
    MatterFactory,
    MatterSharedWithFactory,
)
from ...business.models import Lead, Matter
from .. import factories, models

date_now = arrow.now()


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


@pytest.fixture(scope='module')
def other_matter(
    django_db_blocker, other_client: models.Client, attorney: models.Attorney
) -> Matter:
    """Create matter for testing for other client."""
    with django_db_blocker.unblock():
        return MatterFactory(
            client=other_client,
            attorney=attorney,
            status=Matter.STATUS_OPEN
        )


@pytest.fixture(scope='module')
def user_stat(
    django_db_blocker, attorney: models.Attorney
) -> models.UserStatistic:
    """Create user stat for testing."""
    with django_db_blocker.unblock():
        created = arrow.now().shift(years=-100).datetime
        return models.UserStatistic.objects.create(
            user=attorney.user,
            created=created,
            tag=models.UserStatistic.TAG_OPPORTUNITIES
        )


class TestAppUserQuerySet:
    """Test AppUserQuerySet methods."""

    def test_available_for_share_no_matter(self):
        """Check `available_for_share` method without `matter` param.

        Should return only verified attorney user with active subscription.

        """
        not_verified = factories.AttorneyFactory()
        verified_w_active_subscription = factories.AttorneyVerifiedFactory()
        verified_no_active_subscription = factories.AttorneyVerifiedFactory(
            user__active_subscription=None
        )
        staff = factories.AttorneyFactory(user__is_staff=True)

        qs = models.AppUser.objects.all().available_for_share()
        assert verified_w_active_subscription.user in qs
        assert not_verified.user not in qs
        assert verified_no_active_subscription.user not in qs
        assert staff.user not in qs

    def test_available_for_share_with_matter(self):
        """Check `available_for_share` method with `matter` param.

        Should return only verified attorney user with active subscription,
        excluding already shared ones.

        """
        shared = MatterSharedWithFactory()
        not_verified = factories.AttorneyFactory()
        verified_w_active_subscription = factories.AttorneyVerifiedFactory()
        verified_no_active_subscription = factories.AttorneyVerifiedFactory(
            user__active_subscription=None
        )
        staff = factories.AttorneyFactory(user__is_staff=True)

        qs = models.AppUser.objects.all().available_for_share(
            matter=shared.matter
        )
        assert verified_w_active_subscription.user in qs
        assert shared.user not in qs
        assert not_verified.user not in qs
        assert verified_no_active_subscription.user not in qs
        assert staff.user not in qs

    def test_active(self):
        """Check that only `active` user are returned."""
        active = factories.AppUserFactory()
        not_active = factories.AppUserFactory(is_active=False)

        qs = models.AppUser.objects.all().active()
        assert active in qs
        assert not_active not in qs

    def test_clients(self):
        """Check that only `clients` users are returned."""
        client_user = factories.AppUserWithClientFactory()
        attorney_user = factories.AppUserWithAttorneyFactory()
        staff_user = factories.AppUserFactory()
        support_user = factories.AppUserWithSupportFactory()

        qs = models.AppUser.objects.all().clients()
        assert client_user in qs
        assert attorney_user not in qs
        assert staff_user not in qs
        assert support_user not in qs

    def test_attorneys(self):
        """Check that only `attorneys` users are returned."""
        client_user = factories.AppUserWithClientFactory()
        attorney_user = factories.AttorneyVerifiedFactory().user
        staff_user = factories.AppUserFactory()
        support_user = factories.AppUserWithSupportFactory()

        qs = models.AppUser.objects.all().attorneys()
        assert attorney_user in qs
        assert client_user not in qs
        assert staff_user not in qs
        assert support_user not in qs

    def test_support(self):
        """Check that only `clients` users are returned."""
        client_user = factories.AppUserWithClientFactory()
        attorney_user = factories.AppUserWithAttorneyFactory()
        staff_user = factories.AppUserFactory()
        support_user = factories.PaidSupportFactory().user

        qs = models.AppUser.objects.all().support()
        assert support_user in qs
        assert client_user not in qs
        assert attorney_user not in qs
        assert staff_user not in qs


class TestAttorneyQuerySet:
    """Test AttorneyQuerySet methods."""

    valid_cords = (
        (0, 0),
        (0.0, 0.0),
        ('0', '0.0'),
    )
    invalid_cords = (
        (Point(0, 0), 0),
        (0.0, None),
        ('Test', 'Test'),
    )

    @pytest.mark.parametrize(
        argnames='longitude, latitude',
        argvalues=valid_cords,
    )
    def test_with_distance_method_valid_cords(self, longitude, latitude):
        """Test `with_distance` with valid coordinates."""
        attorneys = models.Attorney.objects.with_distance(
            longitude=longitude,
            latitude=latitude
        )

        assert not attorneys.filter(distance__isnull=True).exists()

    @pytest.mark.parametrize(
        argnames='longitude, latitude',
        argvalues=invalid_cords,
    )
    def test_with_distance_method_invalid_cords(self, longitude, latitude):
        """Test `with_distance` with invalid coordinates."""
        attorneys = models.Attorney.objects.with_distance(
            longitude=longitude,
            latitude=latitude
        )

        assert not attorneys.filter(distance__isnull=False).exists()

    def test_has_lead_with_user(self, lead: Lead):
        """Test 'has_lead_with_user' method."""
        attorneys = models.Attorney.objects.has_lead_with_user(
            user=lead.client.user
        )
        assert lead.attorney in attorneys

    def test_verified(self):
        """Test `verified` method."""
        attorney = factories.AttorneyFactory()
        verified_attorney = factories.AttorneyVerifiedFactory()

        verified_attorneys = models.Attorney.objects.verified()

        assert verified_attorneys.exists()
        assert attorney not in verified_attorneys
        assert verified_attorney in verified_attorneys

    def test_real_users(self):
        """Test `real_users` method."""
        attorney = factories.AttorneyFactory()
        verified_attorney = factories.AttorneyVerifiedFactory()

        staff_attorney = factories.AttorneyFactory(user__is_staff=True)
        staff_verified_attorney = factories.AttorneyVerifiedFactory(
            user__is_staff=True
        )

        real_attorneys = models.Attorney.objects.real_users()

        assert real_attorneys.exists()
        assert attorney in real_attorneys
        assert verified_attorney in real_attorneys
        assert staff_attorney not in real_attorneys
        assert staff_verified_attorney not in real_attorneys


class TestClientQuerySet:
    """Test ClientQuerySet methods."""

    def test_has_lead_with_user(self, lead: Lead):
        """Test 'has_lead_with_user' method."""
        clients = models.Client.objects.has_lead_with_user(
            user=lead.attorney.user
        )
        assert lead.client in clients

    def test_has_matter_with_user_by_attorney(
        self,
        attorney: models.Attorney,
        matter: Matter,
        other_matter: Matter
    ):
        """Test 'has_matter_with_user' method by attorney."""
        shared = MatterSharedWithFactory(
            user=attorney.user, matter__status=Matter.STATUS_OPEN
        )
        clients = models.Client.objects.has_matter_with_user(
            user=attorney.user
        )
        assert matter.client in clients
        assert shared.matter.client in clients
        assert other_matter.client not in clients

    def test_has_matter_with_user_by_support(
        self,
        support: models.Support,
        other_matter: Matter
    ):
        """Test 'has_matter_with_user' method by support."""
        shared = MatterSharedWithFactory(
            user=support.user, matter__status=Matter.STATUS_OPEN
        )
        clients = models.Client.objects.has_matter_with_user(user=support.user)
        assert shared.matter.client in clients
        assert other_matter.client not in clients

    def test_invited_by_user(
        self,
        attorney: models.Attorney,
        invite: models.Invite,
        other_invite: models.Invite
    ):
        """Test `invited_by_user` filter."""
        not_invited_client = factories.ClientFactory()
        clients = models.Client.objects.invited_by_user(user=attorney.user)

        assert clients.exists()
        clients = clients.values_list('pk', flat=True)
        assert invite.user_id in clients.values_list('pk', flat=True)
        assert other_invite.user_id not in clients
        # This client is without invite
        assert not_invited_client.pk not in clients

    def test_user_clients(self, attorney: models.Attorney):
        """Test `user_clients` filter."""
        client = factories.ClientFactory(
            client_type=models.Client.FIRM_TYPE,
            organization_name='test'
        )
        client_by_invite = factories.InviteFactory(
            inviter_id=attorney.pk, user=client.user
        ).user_id
        client_by_lead = LeadFactory(
            attorney_id=attorney.pk, topic=None
        ).client_id
        client_matter = MatterFactory(attorney_id=attorney.pk).client_id
        client_by_shared_matter = MatterSharedWithFactory(
            user=attorney.user
        ).matter.client_id

        clients = models.Client.objects.user_clients(user=attorney.user)

        assert clients.exists()
        clients = clients.values_list('pk', flat=True)

        # This client is connected by invite, matter and lead
        assert client.pk in clients
        # This client is connected by invite
        assert client_by_invite in clients
        # This client is connected by lead
        assert client_by_lead in clients
        # This client is connected by matter
        assert client_matter in clients
        # This client is connected by shared matter
        assert client_by_shared_matter in clients
        # This client is not connected at all
        assert factories.AppUserWithClientFactory().pk not in clients


class TestUserStatisticsQuerySet:
    """Test UserStatisticsQuerySet methods."""

    match_period_data = (
        (
            date_now.shift(years=-100).datetime,
            date_now.shift(years=-100, days=1).datetime,
            models.UserStatistic.TAG_ACTIVE_MATTER,
            False,
            0
        ),
        (
            date_now.shift(years=-100).datetime,
            date_now.shift(years=-100, days=1).datetime,
            models.UserStatistic.TAG_OPPORTUNITIES,
            True,
            1
        ),
        (
            date_now.datetime,
            date_now.datetime,
            models.UserStatistic.TAG_OPPORTUNITIES,
            False,
            0
        ),
    )

    @pytest.mark.parametrize(
        'start, end, tag, expected, expected_count',
        match_period_data
    )
    def test_stats_count_for_tag(
        self,
        user_stat: models.UserStatistic,
        attorney: models.Attorney,
        start: datetime,
        end: datetime,
        tag: str,
        expected: bool,
        expected_count: int
    ):
        """Test `stats_count_for_tag` method."""
        user_stats = models.UserStatistic.objects.for_period(
            user=attorney.user, start_date=start, end_date=end
        ).filter(tag=tag)

        assert (user_stat in user_stats) is expected

        count = models.UserStatistic.objects.stats_count_for_tag(
            user=attorney.user, tag=tag, start_date=start, end_date=end
        )
        assert count == expected_count


class TestInviteQuerySet:
    """Test `InviteQuerySet`."""

    def test_without_user(self):
        """Test `without_user` filter."""
        invite = factories.InviteFactory()
        invite_with_user = factories.InviteFactory(
            user=factories.AppUserFactory()
        )

        invites_without_user = models.Invite.objects.without_user()

        assert invites_without_user.exists()
        assert invite in invites_without_user
        assert invite_with_user not in invites_without_user
