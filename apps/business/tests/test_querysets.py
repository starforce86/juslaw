import typing
from datetime import datetime, timedelta
from decimal import Decimal

import arrow
import pytest
from factory import DjangoModelFactory

from libs.utils import get_datetime_from_str, get_lookup_value

from ...core.models import BaseModel
from ...users.factories import AppUserFactory
from ...users.models import AppUser
from .. import factories, models


@pytest.fixture(scope='session')
def another_note(django_db_blocker) -> models.Note:
    """Create note testing."""
    with django_db_blocker.unblock():
        return factories.NoteFactory()


class TestMatterAndUserRelatedQuerySet:
    """Tests for `MatterRelatedQuerySet` and `UserRelatedQuerySet` methods."""

    available_for_user_data = [
        (factories.LeadFactory, models.Lead, None),
        (factories.MatterFactory, models.Matter, None),
        (factories.BillingItemFactory, models.BillingItem, 'matter'),
        (factories.MatterTopicFactory, models.MatterTopic, 'matter'),
        (factories.MatterPostFactory, models.MatterPost, 'topic.matter'),
        (factories.VoiceConsentFactory, models.VoiceConsent, 'matter'),
        (factories.MatterSharedWithFactory, models.MatterSharedWith, 'matter'),
    ]

    @pytest.mark.parametrize(
        'factory_class,model_class,matter_lookup', available_for_user_data
    )
    @pytest.mark.parametrize(
        'user_type', ('attorney', 'client')
    )
    def test_matter_available_for_user_by_client(
        self,
        factory_class: typing.Type[DjangoModelFactory],
        model_class: typing.Type[BaseModel],
        matter_lookup: str,
        user_type: str
    ):
        """Test `available_for_user` for client and attorney.

        Check matter related querysets for attorney and client.

        """
        # object available to client
        obj = factory_class()
        user_profile = get_lookup_value(obj, f'{matter_lookup}.{user_type}') \
            if matter_lookup else getattr(obj, user_type)
        # object available to another users
        factory_class()

        available = model_class.objects.all().available_for_user(
            user_profile.user
        )
        assert available.count() == 1
        assert available.first() == obj


class TestMatterQuerySet:
    """Tests for `MatterQuerySet` methods."""

    @pytest.mark.parametrize(
        argnames='status, is_available',
        argvalues=(
            (models.Matter.STATUS_OPEN, False),
            (models.Matter.STATUS_CLOSE, True),
        )
    )
    def test_available_for_user(self, matter, status, is_available):
        """Test that shared matters are also available for user."""
        matter.status = status
        matter.save()

        shared = factories.MatterSharedWithFactory(matter=matter)
        available = models.Matter.objects.all().available_for_user(
            shared.user
        )
        if is_available:
            assert matter in available
        else:
            assert matter not in available

    def test_open(self, matter, another_matter):
        """Test `active` matter qs method."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        assert another_matter.status != models.Matter.STATUS_OPEN

        active = models.Matter.objects.all().active()
        assert matter in active

    def test_hourly_rated(self, another_matter):
        """Test `hourly_rated` matter qs method."""
        another_matter.rate_type = models.Matter.RATE_TYPE_FIXED
        another_matter.save()
        hourly = models.Matter.objects.all().hourly_rated()
        assert not hourly.filter(id=another_matter.id).exists()

    def test_with_invoices_num_w_invoices(self, matter):
        """Test `with_invoices_num` matter qs method with invoices."""
        factories.InvoiceFactory(matter=matter)
        instance = models.Matter.objects.all().with_invoices_num() \
            .filter(id=matter.id).first()
        assert instance.num_invoices == matter.invoices.count()

    def test_with_invoices_num_no_invoices(self, matter):
        """Test `with_invoices_num` matter qs method without invoices."""
        matter.invoices.all().delete()
        instance = models.Matter.objects.all().with_invoices_num() \
            .filter(id=matter.id).first()
        assert instance.num_invoices == 0

    def test_with_totals_w_time_billings(self, matter):
        """Test `with_totals` matter qs method with time billings."""
        time_billings = factories.BillingItemFactory.create_batch(
            matter=matter, size=2
        )
        instance = models.Matter.objects.all().with_totals() \
            .filter(id=matter.id).first()

        expected = {'time_billed': timedelta(seconds=0), 'fees_earned': 0}
        for tb in time_billings:
            expected['time_billed'] += tb.time_spent
            expected['fees_earned'] += Decimal("{0:.2f}".format(tb.fees))
        assert instance._time_billed == expected['time_billed']
        assert instance._fees_earned == expected['fees_earned']

    def test_with_totals_no_time_billings(self, matter):
        """Test `with_totals` matter qs method with time billings."""
        matter.billing_item.all().delete()
        instance = models.Matter.objects.all().with_totals() \
            .filter(id=matter.id).first()
        assert instance._time_billed is None
        assert instance._fees_earned is None

    def test_with_is_shared_for_user_by_attorney(self, matter, another_matter):
        """Test `with_is_shared_for_user` matter qs method by attorney."""
        user = factories.MatterSharedWithFactory(matter=matter).user
        qs = models.Matter.objects.all().with_is_shared_for_user(user)
        is_shared = [
            qs.get(id=m.id)._is_shared
            for m in [matter, another_matter]
        ]
        assert is_shared == [True, False]

    def test_with_is_shared_for_user_by_client(self, matter, another_matter):
        """Test `with_is_shared_for_user` matter qs method by client."""
        user = matter.client.user
        factories.MatterSharedWithFactory(matter=matter, user=user)
        qs = models.Matter.objects.all().with_is_shared_for_user(user)
        is_shared = [
            qs.get(id=m.id)._is_shared
            for m in [matter, another_matter]
        ]
        assert is_shared == [True, False]


class TestBillingItemQuerySet:
    """Tests for `TestBillingItemQuerySet` methods."""

    match_period_data = [
        # case when period matches -> returned
        (datetime.now() - timedelta(days=1), True),
        # case when period doesn't match -> not returned
        (datetime.now() + timedelta(days=7), False),
    ]

    @pytest.mark.parametrize('date,expected', match_period_data)
    def test_match_period(self, date, expected, matter):
        """Test `match_period` filters correct results.

        This test manipulates `datetime.now()` dates as far as for old dates
        invoices are automatically generated.

        """
        matter.invoices.all().delete()
        factories.BillingItemFactory(matter=matter, date=date)
        period_start = datetime.now() - timedelta(days=1)
        period_end = datetime.now() + timedelta(days=1)
        time_billings = models.BillingItem.objects.filter(matter=matter) \
            .match_period(period_start=period_start, period_end=period_end)
        assert time_billings.count() == (1 if expected else 0)

    def test_calculate_time_billing_for_period(self, matter, another_matter):
        """Test `calculate_time_billing_for_period` returns correct data."""
        matter.billing_item.all().delete()
        # available for user TB with fit date -> should be counted
        tb_with_fit_date = factories.BillingItemFactory(
            matter=matter, date=get_datetime_from_str('2019-02-14')
        )
        # available for user TB with not fit date -> shouldn't be counted
        factories.BillingItemFactory(
            matter=matter, date=get_datetime_from_str('2019-01-01')
        )
        # not available for user TB with fit date -> shouldn't be counted
        factories.BillingItemFactory(
            matter=another_matter, date=get_datetime_from_str('2019-02-14')
        )
        # available for user TB with fit date and 0 time -> should be counted
        tb_with_zero_time_spent = factories.BillingItemFactory(
            matter=matter,
            date=get_datetime_from_str('2019-02-14'),
            time_spent=timedelta(seconds=0)
        )
        time_spent_sum = models.BillingItem.objects.all() \
            .calculate_time_billing_for_period(
            user=matter.attorney.user,
            start_date=get_datetime_from_str('2019-02-01'),
            end_date=get_datetime_from_str('2019-02-28')
        )
        expected_sum = (
            tb_with_fit_date.time_spent + tb_with_zero_time_spent.time_spent
        )
        assert time_spent_sum == expected_sum

    def test_get_total_fee_not_hourly_rated_matter(self, another_matter):
        """Test `get_total_fee` method for not hourly rated matter.

        Check that even if BillingItem qs is related to one matter and the
        matter is not of `hourly` rated type there will be return `None`.

        """
        another_matter.rate_type = models.Matter.RATE_TYPE_ALTERNATIVE
        another_matter.save()
        factories.BillingItemFactory(matter=another_matter)
        total_fee = another_matter.billing_item.all().get_total_fee()
        assert total_fee is None

    def test_get_total_fee_hourly_rated_matter(self, matter):
        """Test `get_total_fee` method for hourly rated matter.

        Check that even if BillingItem qs is related to one matter, but with
        hourly rated type its total fees sum will be calculated.

        """
        assert matter.rate_type == models.Matter.RATE_TYPE_HOURLY
        factories.BillingItemFactory(matter=matter)
        expected = sum([
            Decimal("{0:.2f}".format(tb.fees))
            for tb in matter.billing_item.all()
        ])
        total_fee = matter.billing_item.all().get_total_fee()
        assert expected == total_fee

    def test_get_total_fee_different_matters_qs(self, matter, another_matter):
        """Test `get_total_fee` method for different matters qs

        Check that for BillingItem qs related to few matters its total fees
        sum will be calculated for matter with any `rate_type`.

        """
        another_matter.rate_type = models.Matter.RATE_TYPE_ALTERNATIVE
        another_matter.save()

        factories.BillingItemFactory(matter=matter)
        factories.BillingItemFactory(matter=another_matter)
        expected = sum([
            Decimal("{0:.2f}".format(tb.fees))
            for tb in models.BillingItem.objects.all()
        ])
        total_fee = models.BillingItem.objects.all().get_total_fee()
        assert expected == total_fee

    def test_get_total_time_qs_with_time_billings(
        self, matter, another_matter
    ):
        """Test `get_total_time` method on qs with existing time billings.

        There should be returned a sum of `time_spent` in string
        representation.

        """
        factories.BillingItemFactory(matter=matter)
        factories.BillingItemFactory(matter=another_matter)

        total_time = models.BillingItem.objects.all().get_total_time()
        expected = timedelta(seconds=0)
        for tb in models.BillingItem.objects.all():
            expected += tb.time_spent
        assert total_time == str(expected)

    def test_get_total_time_qs_no_time_billings(self, matter, another_matter):
        """Test `get_total_time` method on qs with no time billings.

        There should be returned a '00:00:00' value for such cases.

        """
        total_time = models.BillingItem.objects.none().get_total_time()
        assert total_time == '00:00:00'

    def test_available_for_editing(
        self,
        to_be_paid_time_billing: models.BillingItem,
        not_paid_time_billing: models.BillingItem,
        paid_time_billing: models.BillingItem,
    ):
        """Test 'available_for_editing' method."""
        available_for_edit_tb = models.BillingItem.objects. \
            available_for_editing()
        assert not_paid_time_billing in available_for_edit_tb
        assert to_be_paid_time_billing not in available_for_edit_tb
        assert paid_time_billing not in available_for_edit_tb

    def test_with_available_for_editing(
        self,
        to_be_paid_time_billing: models.BillingItem,
        not_paid_time_billing: models.BillingItem,
        paid_time_billing: models.BillingItem,
    ):
        """Test 'with_available_for_editing' method."""
        result = list(
            models.BillingItem.objects.with_available_for_editing().order_by(
                'pk'
            ).values_list('_available_for_editing', flat=True).filter(pk__in=(
                not_paid_time_billing.pk,
                to_be_paid_time_billing.pk,
                paid_time_billing.pk,
            ))
        )
        expected = [
            tb.available_for_editing for tb in sorted([
                not_paid_time_billing,
                to_be_paid_time_billing,
                paid_time_billing
            ], key=lambda x: x.pk)
        ]
        assert result == expected

    def test_with_is_paid(
        self,
        to_be_paid_time_billing: models.BillingItem,
        not_paid_time_billing: models.BillingItem,
        paid_time_billing: models.BillingItem,
    ):
        """Test 'with_is_paid' method."""
        result = list(
            models.BillingItem.objects.with_is_paid().order_by(
                'pk'
            ).values_list('_is_paid', flat=True).filter(pk__in=(
                not_paid_time_billing.pk,
                to_be_paid_time_billing.pk,
                paid_time_billing.pk,
            ))
        )
        expected = [
            tb.is_paid for tb in sorted([
                not_paid_time_billing,
                to_be_paid_time_billing,
                paid_time_billing
            ], key=lambda x: x.pk)
        ]
        assert result == expected


class TestInvoiceQuerySet:
    """Tests for `TestInvoiceQuerySet` methods."""

    def test_match_date(self, matter: models.Matter):
        """Test `match_date` filters correct results."""
        matter.invoices.all().delete()
        date = datetime.now()
        # matching invoice
        expected = factories.InvoiceFactory(
            matter=matter,
            period_start=date - timedelta(days=1),
            period_end=date + timedelta(days=1),
        )
        # not matching invoice which period starts later
        factories.InvoiceFactory(
            matter=matter,
            period_start=date + timedelta(days=1),
            period_end=date + timedelta(days=2),
        )
        # not matching invoice which period ends before
        factories.InvoiceFactory(
            matter=matter,
            period_start=date - timedelta(days=2),
            period_end=date - timedelta(days=1),
        )

        invoices = models.Invoice.objects.filter(
            matter=matter
        ).match_date(date=date)
        assert invoices.count() == 1
        assert invoices.first().id == expected.id

    def test_match_period(self, matter: models.Matter):
        """Test `match_period` method."""
        matter.invoices.all().delete()
        start_date = arrow.utcnow()
        end_date = start_date.shift(months=1)
        # Matching invoices
        # Invoice which period ends inside input period
        between_start = factories.InvoiceFactory(
            matter=matter,
            period_start=start_date.shift(days=-1).datetime,
            period_end=start_date.shift(days=1).datetime,
        )
        # Invoice which period starts inside input period
        between_end = factories.InvoiceFactory(
            matter=matter,
            period_start=end_date.shift(days=-1).datetime,
            period_end=end_date.shift(days=1).datetime,
        )
        # Invoice which is inside input period
        between_start_and_end = factories.InvoiceFactory(
            matter=matter,
            period_start=start_date.shift(days=1).datetime,
            period_end=end_date.shift(days=-1).datetime,
        )
        # Invoice which has input period inside itself
        outside_start_and_end = factories.InvoiceFactory(
            matter=matter,
            period_start=start_date.shift(days=-1).datetime,
            period_end=end_date.shift(days=1).datetime,
        )
        # Not matching invoice which period start and end are less than start
        # date
        mismatch_left = factories.InvoiceFactory(
            matter=matter,
            period_start=start_date.shift(days=-1).datetime,
            period_end=start_date.shift(days=-1).datetime,
        )
        # Not matching invoice which period start and end are bigger than end
        # date
        mismatch_right = factories.InvoiceFactory(
            matter=matter,
            period_start=end_date.shift(days=1).datetime,
            period_end=end_date.shift(days=1).datetime,
        )

        invoices = models.Invoice.objects.filter(
            matter=matter
        ).match_period(
            period_start=start_date.datetime,
            period_end=end_date.datetime
        )
        assert invoices.count() == 4
        assert between_start in invoices
        assert between_end in invoices
        assert between_start_and_end in invoices
        assert outside_start_and_end in invoices
        assert mismatch_left not in invoices
        assert mismatch_right not in invoices

    def test_match_period_invalid_input(self, matter: models.Matter):
        """Test `match_period` method with incorrect period.

        Test case when start and end dates are swapped.

        """
        matter.invoices.all().delete()
        start_date = arrow.utcnow()
        end_date = start_date.shift(months=1)
        # Matching invoice
        factories.InvoiceFactory(
            matter=matter,
            period_start=start_date.shift(days=-1).datetime,
            period_end=start_date.shift(days=1).datetime,
        )
        invoices = models.Invoice.objects.filter(
            matter=matter
        ).match_period(
            period_start=end_date.datetime,
            period_end=start_date.datetime
        )
        assert not invoices.count()

    def test_available_for_editing(
        self,
        pending_invoice: models.Invoice,
        sent_invoice: models.Invoice,
        paid_invoice: models.Invoice,
        to_be_paid_invoice: models.Invoice,
    ):
        """Test 'available_for_editing' method."""
        available_for_edit_invoices = models.Invoice.objects. \
            available_for_editing()
        assert pending_invoice in available_for_edit_invoices
        assert sent_invoice in available_for_edit_invoices
        assert to_be_paid_invoice not in available_for_edit_invoices
        assert paid_invoice not in available_for_edit_invoices


class TestNoteQuerySet:
    """Tests for `NoteQuerySet` methods."""

    def test_available_for_user_by_client(self, matter, another_note):
        """Test `available_for_user` by client AppUser."""
        # object available to client
        note = factories.NoteFactory(
            matter=matter,
            created_by=matter.client.user
        )
        available = models.Note.objects.all().available_for_user(
            user=matter.client.user
        )
        assert available.count() == 1
        assert available.first() == note

    def test_available_for_user_by_attorney(self, matter, another_note):
        """Test `available_for_user` by attorney AppUser."""
        # object available to attorney
        note = factories.NoteFactory(
            matter=matter, created_by=matter.attorney.user
        )
        available = models.Note.objects.all().available_for_user(
            matter.attorney.user
        )
        assert available.count() == 1
        assert available.first() == note


class TestVideoCallQuerySet:
    """Tests for `VideoCallQuerySet` methods."""

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney'
        ),
        indirect=True
    )
    def test_available_for_user(
        self,
        user: AppUser,
        attorney_video_call: models.VideoCall,
        other_video_call: models.VideoCall,
    ):
        """Test `available_for_user` method."""
        available = models.VideoCall.objects.available_for_user(
            user=user
        )
        assert attorney_video_call in available
        assert other_video_call not in available

    def test_get_by_participants(self):
        """Test `get_by_participants` method."""
        app_users = AppUserFactory.create_batch(size=3)

        video_call_with_two = models.VideoCall.objects.create()
        video_call_with_two.participants.set(app_users[:1])

        video_call_from_qs = models.VideoCall.objects.get_by_participants(
            participants=app_users[:1]
        )
        assert video_call_from_qs.pk == video_call_with_two.pk

        video_call_with_two = models.VideoCall.objects.create()
        video_call_with_two.participants.set(app_users[1:])

        video_call_from_qs = models.VideoCall.objects.get_by_participants(
            participants=app_users[1:]
        )
        assert video_call_from_qs.pk == video_call_with_two.pk

        video_call_with_three = models.VideoCall.objects.create()
        video_call_with_three.participants.set(app_users)

        video_call_from_qs = models.VideoCall.objects.get_by_participants(
            participants=app_users
        )
        assert video_call_from_qs.pk == video_call_with_three.pk
