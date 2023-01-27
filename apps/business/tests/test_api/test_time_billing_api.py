from datetime import datetime, timedelta

from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import (
    BAD_REQUEST,
    CREATED,
    FORBIDDEN,
    NO_CONTENT,
    NOT_FOUND,
    OK,
)

from ....users.models import AppUser
from ... import models
from ...api import serializers
from ...factories import InvoiceFactory


def get_list_url():
    """Get url for time-billing creation and list retrieval."""
    return reverse_lazy('v1:time-billing-list')


def get_detail_url(time_billing: models.BillingItem):
    """Get url for time-billing editing and retrieval."""
    return reverse_lazy(
        'v1:time-billing-detail', kwargs={'pk': time_billing.pk}
    )


class TestAuthUserAPI:
    """Test time billing api for auth users.

    Attorney have full CRUD access for TB in owned or shared with them matters.
    Client have read only access.
    Support have full CRUD access for TB in shared with them matters.

    """

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney',
            # shared attorney and support
            'support',
            'shared_attorney',
        ),
        indirect=True
    )
    def test_get_list_time_billing(self, api_client: APIClient, user: AppUser):
        """Test that users can get list of time billings."""
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == OK, response.data

        if response.status_code != OK:
            return
        billings_expected = set(
            models.BillingItem.objects.available_for_user(
                user=user
            ).values_list(
                'pk', flat=True
            )
        )
        billings_result = set(
            billings_data['id'] for billings_data in response.data['results']
        )
        assert billings_result == billings_expected

    @pytest.mark.parametrize(
        argnames='user, time_billing, status_code',
        argvalues=(
            ('client', 'not_paid_time_billing', OK),
            ('client', 'paid_time_billing', OK),
            ('client', 'to_be_paid_time_billing', OK),
            # Test that client doesn't have access to foreign tb
            ('client', 'other_time_billing', NOT_FOUND),

            ('attorney', 'not_paid_time_billing', OK),
            ('attorney', 'paid_time_billing', OK),
            ('attorney', 'to_be_paid_time_billing', OK),
            # Test that attorney doesn't have access to foreign tb
            ('attorney', 'other_time_billing', NOT_FOUND),

            # shared attorney and support

            ('support', 'not_paid_time_billing', OK),
            ('support', 'paid_time_billing', OK),
            ('support', 'to_be_paid_time_billing', OK),
            # Test that doesn't have access to foreign tb
            ('support', 'other_time_billing', NOT_FOUND),

            ('shared_attorney', 'not_paid_time_billing', OK),
            ('shared_attorney', 'paid_time_billing', OK),
            ('shared_attorney', 'to_be_paid_time_billing', OK),
            # Test that doesn't have access to foreign tb
            ('shared_attorney', 'other_time_billing', NOT_FOUND)  # noqa
        ),
        indirect=True
    )
    def test_retrieve_time_billing(
        self, api_client: APIClient, user: AppUser, status_code: int,
        time_billing: models.BillingItem, matter: models.Matter
    ):
        """Test that users can get details of time billing."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        url = get_detail_url(time_billing)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == status_code, response.data

        if status_code != OK:
            return

        models.BillingItem.objects.available_for_user(
            user=user
        ).get(pk=response.data['id'])

    def test_create_time_billing_by_client(
        self, auth_client_api: APIClient,
        not_paid_time_billing: models.BillingItem
    ):
        """Test that clients can't create new time billings."""
        time_billing_json = serializers.BillingItemSerializer(
            instance=not_paid_time_billing
        ).data
        url = get_list_url()
        response = auth_client_api.post(url, time_billing_json)
        assert response.status_code == FORBIDDEN

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'attorney',
            # shared attorney and support
            'support',
            'shared_attorney',
        ),
        indirect=True
    )
    def test_create_time_billing_with_invoice_not_matching_period(
        self, api_client: APIClient, user: AppUser, matter: models.Matter
    ):
        """Test TB creation by user with invoice.

        When TB is created with invoice and not matching period - API should
        raise validation error.

        """
        invoice = InvoiceFactory(matter=matter)
        time_billing_json = {
            'matter': invoice.matter_id,
            'description': 'Test',
            'time_spent': '00:25:00',
            'date': (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d'),
            'invoice': invoice.id
        }
        api_client.force_authenticate(user=user)
        resp = api_client.post(get_list_url(), time_billing_json)
        assert resp.status_code == BAD_REQUEST, resp.data

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'attorney',
            # shared attorney and support
            'support',
            'shared_attorney',
        ),
        indirect=True
    )
    def test_create_time_billing_with_invoice_matching_period(
        self, api_client: APIClient, user: AppUser, matter: models.Matter
    ):
        """Test TB creation by user with invoice.

        When TB is created with invoice and matching period - API should attach
        new time billing to defined invoice.

        """
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        invoice = InvoiceFactory(
            period_start=datetime.now() - timedelta(days=40),
            period_end=datetime.now() - timedelta(days=30),
            matter=matter
        )
        assert invoice.attached_time_billing.count() == 0

        time_billing_json = {
            'matter': invoice.matter_id,
            'description': 'Test',
            'time_spent': '00:25:00',
            'date': (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d'),
            'invoice': invoice.id
        }

        api_client.force_authenticate(user=user)
        resp = api_client.post(get_list_url(), time_billing_json)
        assert resp.status_code == CREATED, resp.data
        assert invoice.attached_time_billing.count() == 1
        assert (
            invoice.attached_time_billing.first()
            .time_billing_id == resp.data['id']
        )

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'attorney',
            # shared attorney and support
            'support',
            'shared_attorney',
        ),
        indirect=True
    )
    def test_create_time_billing_without_invoice(
        self, api_client: APIClient, user: AppUser, matter: models.Matter
    ):
        """Test TB creation by user without invoice.

        When TB is created without invoice - API should automatically attach
        it to corresponding by dates invoices.

        """
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        not_matching_period = InvoiceFactory(matter=matter)
        matching_period_1 = InvoiceFactory(
            matter=matter,
            period_start=datetime.now() - timedelta(days=36),
            period_end=datetime.now() - timedelta(days=30)
        )
        matching_period_2 = InvoiceFactory(
            matter=matter,
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now() - timedelta(days=20)
        )
        time_billing_json = {
            'matter': not_matching_period.matter_id,
            'description': 'Test',
            'time_spent': '00:25:00',
            'date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        }
        api_client.force_authenticate(user=user)
        resp = api_client.post(get_list_url(), time_billing_json)
        assert resp.status_code == CREATED

        instance = models.BillingItem.objects.filter(
            id=resp.data['id']
        ).first()
        assert instance.attached_invoice.count() == 2
        assert instance.attached_invoice.filter(
            invoice__id__in=[matching_period_1.id, matching_period_2.id]
        ).count() == 2

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'attorney',
            # shared attorney and support
            'support',
            'shared_attorney',
        ),
        indirect=True
    )
    def test_create_foreign_time_billing(
        self, api_client: APIClient, another_matter: models.Matter,
        user: AppUser
    ):
        """Test that user can't create time billing in foreign matters."""
        time_billing_json = {
            'matter': another_matter.id,
            'description': 'Test',
            'time_spent': '00:25:00',
            'date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        }
        api_client.force_authenticate(user=user)
        resp = api_client.post(get_list_url(), time_billing_json)
        assert resp.status_code == BAD_REQUEST

    @pytest.mark.parametrize(
        argnames='user, time_billing, status_code',
        argvalues=(
            ('client', 'not_paid_time_billing', FORBIDDEN),
            ('client', 'paid_time_billing', FORBIDDEN),
            ('client', 'to_be_paid_time_billing', FORBIDDEN),
            # Test that client doesn't have access to foreign tb
            ('client', 'other_time_billing', FORBIDDEN),

            ('attorney', 'not_paid_time_billing', OK),
            ('attorney', 'paid_time_billing', FORBIDDEN),
            ('attorney', 'to_be_paid_time_billing', FORBIDDEN),
            # Test that attorney doesn't have access to foreign tb
            ('attorney', 'other_time_billing', NOT_FOUND),

            # shared attorney and support

            ('support', 'not_paid_time_billing', OK),
            ('support', 'paid_time_billing', FORBIDDEN),
            ('support', 'to_be_paid_time_billing', FORBIDDEN),
            # Test that attorney doesn't have access to foreign tb
            ('support', 'other_time_billing', NOT_FOUND),

            ('shared_attorney', 'not_paid_time_billing', OK),
            ('shared_attorney', 'paid_time_billing', FORBIDDEN),
            ('shared_attorney', 'to_be_paid_time_billing', FORBIDDEN),
            # Test that attorney doesn't have access to foreign tb
            ('shared_attorney', 'other_time_billing', NOT_FOUND),
        ),
        indirect=True
    )
    def test_edit_time_billing(
        self, user: AppUser, api_client: APIClient,
        time_billing: models.BillingItem, status_code: int,
        matter: models.Matter
    ):
        """Test that edit logic of time billings."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        time_billing_json = serializers.BillingItemSerializer(
            instance=time_billing
        ).data
        description = 'test time billing editing'
        time_billing_json['description'] = description
        url = get_detail_url(time_billing)
        api_client.force_authenticate(user=user)
        response = api_client.put(url, time_billing_json)

        assert response.status_code == status_code, response.data

    @pytest.mark.parametrize(
        argnames='user, time_billing, status_code',
        argvalues=(
            ('client', 'not_paid_time_billing', FORBIDDEN),
            ('client', 'paid_time_billing', FORBIDDEN),
            ('client', 'to_be_paid_time_billing', FORBIDDEN),
            ('client', 'other_time_billing', FORBIDDEN),

            ('attorney', 'not_paid_time_billing', NO_CONTENT),
            ('attorney', 'paid_time_billing', FORBIDDEN),
            ('attorney', 'to_be_paid_time_billing', FORBIDDEN),
            ('attorney', 'other_time_billing', NOT_FOUND),

            # shared attorney and support

            ('support', 'not_paid_time_billing', NO_CONTENT),
            ('support', 'paid_time_billing', FORBIDDEN),
            ('support', 'to_be_paid_time_billing', FORBIDDEN),
            ('support', 'other_time_billing', NOT_FOUND),

            ('shared_attorney', 'not_paid_time_billing', NO_CONTENT),
            ('shared_attorney', 'paid_time_billing', FORBIDDEN),
            ('shared_attorney', 'to_be_paid_time_billing', FORBIDDEN),
            ('shared_attorney', 'other_time_billing', NOT_FOUND),
        ),
        indirect=True
    )
    def test_delete_time_billing(
        self, api_client: APIClient, user: AppUser, status_code: int,
        time_billing: models.BillingItem, matter: models.Matter
    ):
        """Test that users can delete billed time."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        url = get_detail_url(time_billing)
        api_client.force_authenticate(user=user)
        response = api_client.delete(url)
        assert response.status_code == status_code
