from django.urls import reverse

from rest_framework.test import APIClient

import arrow
import pytest
from cities_light.management.commands import cities_light
from faker import Faker

from libs.testing.constants import BAD_REQUEST, FORBIDDEN, OK

from ...models import AppUser, Attorney, Client, Support


class TestAttorneyAPI:
    """Test `current attorney` api."""

    @property
    def profile_url(self):
        """Get url to current attorney profile."""
        return reverse('v1:current_attorney')

    @property
    def current_statistics_url(self):
        """Get url to attorney current statistics."""
        return reverse('v1:current_attorney_actions-current-statistics')

    def period_statistics_url(self, start: arrow, end: arrow):
        """Get url to attorney period statistics."""
        url = reverse('v1:current_attorney_actions-period-statistics')
        start = start.datetime.replace(tzinfo=None).isoformat()
        end = end.datetime.replace(tzinfo=None).isoformat()
        return f'{url}?start={start}&end={end}'

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('attorney', OK),
            ('support', FORBIDDEN),
            ('client', FORBIDDEN),
        ),
        indirect=True
    )
    def test_get_profile(
        self, api_client: APIClient, user: AppUser, attorney: Attorney,
        status_code: int
    ):
        """Test getting current attorney profile for different user types."""
        api_client.force_authenticate(user=user)
        response = api_client.get(self.profile_url)
        assert response.status_code == status_code, response.data

        # Check that correct profile was returned
        if status_code == OK:
            assert attorney.pk == response.data['id']

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('attorney', OK),
            ('support', FORBIDDEN),
            ('client', FORBIDDEN),
        ),
        indirect=True
    )
    def test_update_profile(
        self, api_client: APIClient, user: AppUser, attorney: Attorney,
        status_code: int
    ):
        """Test that attorney user can update it's profile."""
        fake = Faker()
        existing_attachments = \
            attorney.registration_attachments.first().attachment
        new_attachment = attorney.user.avatar
        data = {
            'email': fake.email(),
            'years_of_experience': 20,
            'keywords': ['test1', 'test2'],
            'registration_attachments': [
                f'http://localhost{existing_attachments.url}',
                f'http://localhost{new_attachment.url}',
            ]
        }

        api_client.force_authenticate(user=user)
        response = api_client.patch(self.profile_url, data)
        assert response.status_code == status_code, response.data

        # Check that correct support profile was returned
        if status_code == OK:
            assert attorney.pk == response.data['id']
            attorney.refresh_from_db()
            attorney.user.refresh_from_db()

            assert attorney.user.email != data['email']
            assert attorney.years_of_experience == data['years_of_experience']
            assert attorney.email != data['email']
            assert attorney.keywords == data['keywords']

            # Check that attachments was updated
            assert attorney.registration_attachments.count() == 2
            assert attorney.registration_attachments.filter(
                attachment=existing_attachments.name
            ).exists()
            assert attorney.registration_attachments.filter(
                attachment=new_attachment.name
            ).exists()

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('attorney', OK),
            ('support', FORBIDDEN),
            ('client', FORBIDDEN),
        ),
        indirect=True
    )
    def test_get_current_statistics(
        self, api_client: APIClient, user: AppUser, status_code: int
    ):
        """Test that attorney can get it's currents statistics."""
        api_client.force_authenticate(user=user)
        response = api_client.get(self.current_statistics_url)
        assert response.status_code == status_code

        # Check that all information returned correctly
        if status_code == OK:
            assert 'active_leads_count' in response.data
            assert 'active_matters_count' in response.data
            assert 'opportunities_count' in response.data
            assert 'documents_count' in response.data

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('attorney', OK),
            ('support', FORBIDDEN),
            ('client', FORBIDDEN),
        ),
        indirect=True
    )
    def test_get_period_statistics(
        self, api_client: APIClient, user: AppUser, status_code: int
    ):
        """Test that attorney can get it's period statistics."""
        end = arrow.now()
        start = end.shift(months=-1)
        url = self.period_statistics_url(start=start, end=end)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status_code

    def test_get_period_statistics_invalid_params(
        self, auth_attorney_api: APIClient
    ):
        """Test that attorney must use correct start and dates for stats."""
        start = arrow.now()
        end = start.shift(months=-1)
        url = self.period_statistics_url(start=start, end=end)

        response = auth_attorney_api.get(url)

        assert response.status_code == BAD_REQUEST

        # Check that invalid fields is start
        assert 'non_field_errors' in response.data['data']


class TestClientAPI:
    """Test `current client` api."""

    @property
    def profile_url(self):
        """Get url to current client profile."""
        return reverse('v1:current_client')

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', OK),
            ('support', FORBIDDEN),
            ('attorney', FORBIDDEN),
        ),
        indirect=True
    )
    def test_get_profile(
        self, api_client: APIClient, user: AppUser, client: Client,
        status_code: int
    ):
        """Test getting current client profile for different user types."""
        api_client.force_authenticate(user=user)
        response = api_client.get(self.profile_url)
        assert response.status_code == status_code, response.data

        # Check that correct profile was returned
        if status_code == OK:
            assert client.pk == response.data['id']

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', OK),
            ('support', FORBIDDEN),
            ('attorney', FORBIDDEN),
        ),
        indirect=True
    )
    def test_update_profile(
        self, api_client: APIClient, user: AppUser, client: Client,
        status_code: int
    ):
        """Test that client user can update it's profile."""
        fake = Faker()
        data = {
            'email': fake.email(),
            'state': cities_light.Region.objects.first().pk,
            'help_description': 'Test help description',
        }

        api_client.force_authenticate(user=user)
        response = api_client.patch(self.profile_url, data)
        assert response.status_code == status_code, response.data

        # Check that correct profile was returned
        if status_code == OK:
            assert client.pk == response.data['id']
            client.refresh_from_db()
            client.user.refresh_from_db()

            assert client.email != data['email']
            assert client.state_id == data['state']
            assert client.help_description == data['help_description']


class TestSupportAPI:
    """Test `current support` api."""

    @property
    def profile_url(self):
        """Get url to current support profile."""
        return reverse('v1:current_support')

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('support', OK),
            ('attorney', FORBIDDEN),
            ('client', FORBIDDEN),
        ),
        indirect=True
    )
    def test_get_profile(
        self, api_client: APIClient, user: AppUser, support: Support,
        status_code: int
    ):
        """Test getting current support profile for different user types."""
        api_client.force_authenticate(user=user)
        response = api_client.get(self.profile_url)
        assert response.status_code == status_code, response.data

        # Check that support profile was returned
        if status_code == OK:
            assert support.pk == response.data['id']

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('support', OK),
            ('attorney', FORBIDDEN),
            ('client', FORBIDDEN),
        ),
        indirect=True
    )
    def test_update_profile(
        self, api_client: APIClient, user: AppUser, support: Support,
        status_code: int
    ):
        """Test that support user can update it's profile."""
        fake = Faker()
        data = {
            'email': fake.email(),
            'description': 'Test description',
        }

        api_client.force_authenticate(user=user)
        response = api_client.patch(self.profile_url, data)
        assert response.status_code == status_code, response.data

        # Check that correct profile was returned
        if status_code == OK:
            assert support.pk == response.data['id']
            support.refresh_from_db()
            support.user.refresh_from_db()

            assert support.email != data['email']
            assert support.description == data['description']
