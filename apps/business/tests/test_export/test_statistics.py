import csv

from django.db.models import Sum

import arrow

from ....users.factories import AttorneyFactory
from ...export import AttorneyPeriodBusinessResource
from ...factories import FullMatterFactory
from ...models import Matter


def test_attorney_period_business_resource():
    """Test AttorneyPeriodBusinessResource."""
    # Prepare export parameters and data
    attorney = AttorneyFactory()
    FullMatterFactory.create_batch(size=2, attorney=attorney)
    period_start = arrow.utcnow().shift(years=-1).datetime
    period_end = arrow.utcnow().shift(years=1).datetime

    # Perform the export
    export_data = AttorneyPeriodBusinessResource(
        instance=attorney.user,
        extension='csv',
        period_start=period_start,
        period_end=period_end,
    )

    # Parse csv data and compare it to actual
    csv_reader = csv.reader(export_data.export().splitlines())
    matters = Matter.objects.with_time_billings(
        user=attorney.user, period_start=period_start, period_end=period_end
    ).order_by('client').prefetch_related('client')
    for number, row in enumerate(csv_reader):
        # Check first row
        if number == 0:
            assert row == [
                'Period', f'{period_start} - {period_end}', '', '',
            ]
            continue
        # Check second row
        if number == 1:
            assert row == [
                'Client', 'Matter', 'Logged time', 'Earned'
            ]
            continue
        # Check last row
        if number - 2 == matters.count():
            total = matters.aggregate(
                total_attorney_time=Sum('attorney_time_spent'),
                total_attorney_fees=Sum('attorney_fees')
            )
            assert row == [
                '',
                'Total',
                export_data.format_timedelta(total['total_attorney_time']),
                str(total['total_attorney_fees']),
            ]
            continue
        # Check matters data
        matter = matters[number - 2]
        attorney_time_spent = export_data.format_timedelta(
            matter.attorney_time_spent
        )
        assert row == [
            matter.client.full_name,
            matter.title,
            attorney_time_spent,
            str(matter.attorney_fees)
        ]
