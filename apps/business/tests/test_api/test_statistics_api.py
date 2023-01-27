from django.urls import reverse_lazy

from rest_framework.test import APIClient

import arrow

from libs.testing.constants import OK


def get_statistics_export_utl():
    """Get url for statistics retrieval."""
    return reverse_lazy('v1:business-statistics-export')


def test_export_statistics(auth_attorney_api: APIClient):
    """Test that attorney can get export file of business stats."""
    url = get_statistics_export_utl()
    now_time = arrow.now()
    past_time = now_time.shift(years=-1)
    query_params = {
        'period_start': past_time.strftime('%Y-%m-%d'),
        'period_end': now_time.strftime('%Y-%m-%d'),
        'extension': 'csv',
    }

    response = auth_attorney_api.get(url, query_params)

    assert response.status_code == OK

    # Check that file was attached to response
    file_name = (
        f'(Jus-Law) Business report for '
        f"{past_time.strftime('%Y-%m-%d')} - {now_time.strftime('%Y-%m-%d')}"
    )
    content_disposition = f'attachment;filename="{file_name}.csv"'
    content_disposition_from_response = response.get('Content-Disposition')

    assert 'text/csv; charset=utf-8' == response.get('Content-Type')
    assert content_disposition == content_disposition_from_response
