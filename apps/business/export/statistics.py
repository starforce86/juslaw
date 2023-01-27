from datetime import datetime
from typing import Union

from django.db.models import Sum

import tablib

from libs.export.resources import ExcelResource

from ...users.models import AppUser
from .. import models


class AttorneyPeriodBusinessResource(ExcelResource):
    """Resource for period business statistics Excel export for attorney."""

    def __init__(
        self,
        instance: AppUser,
        extension: str,
        period_start: datetime,
        period_end: datetime
    ):
        """Init resource."""
        super().__init__(instance, extension)
        self.instance: AppUser = self.instance
        self.period_start = period_start
        self.period_end = period_end

    @property
    def filename(self) -> str:
        """Prepare filename for export."""
        return (
            f'(Jus-Law) Business report for '
            f'{self.period_start} - {self.period_end}'
            f'.{self.extension}'
        )

    def export(self) -> Union[bytes, str]:
        """Export data as excel file.

        First we create dataset and set two first rows, one shows info about
        period, and second shows table headers. After that we use
        fill_matters_stats method to fill dataset with all needed stats data.

        """
        data = tablib.Dataset()
        data.append(
            ('Period', f'{self.period_start} - {self.period_end}', '', '')
        )
        data.append(('Client', 'Matter', 'Logged time', 'Earned',))
        self.fill_matters_stats(data=data)
        return self.convert_to_bytes(data)

    def fill_matters_stats(self, data: tablib.Dataset):
        """Fill dataset with business stats."""
        matters = models.Matter.objects.with_time_billings(
            user=self.instance,
            period_start=self.period_start,
            period_end=self.period_end,
        ).filter(
            time_spent__isnull=False
        ).order_by('client').prefetch_related('client')
        client_id = None
        for matter in matters:
            # We add client's name only once
            client_name = '' if client_id == matter.client_id \
                else matter.client.full_name
            client_id = matter.client_id
            attorney_time_spent = self.format_timedelta(
                matter.attorney_time_spent
            )
            attorney_fees = matter.attorney_fees or '0.0'
            data.append((
                client_name,
                matter.title,
                attorney_time_spent,
                attorney_fees
            ))
        # Calculate total fees and time_spent and add it to dataset
        total = matters.aggregate(
            total_attorney_time=Sum('attorney_time_spent'),
            total_attorney_fees=Sum('attorney_fees')
        )
        total_attorney_time = self.format_timedelta(
            total['total_attorney_time']
        )
        total_attorney_fees = total['total_attorney_fees'] or '0.0'
        data.append(('', 'Total', total_attorney_time, total_attorney_fees))
