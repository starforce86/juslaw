from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import FORBIDDEN, NO_CONTENT, OK, UNAUTHORIZED

from ...factories import AttorneyVerifiedFactory
from ...models import AppUser, Attorney


def get_list_url(api_name: str):
    """Get url for list retrieval."""
    url_map = {
        'attorney_api': reverse_lazy('v1:attorneys-list'),
        'client_api': reverse_lazy('v1:clients-list'),
        'support_api': reverse_lazy('v1:support-list'),
        'user_api': reverse_lazy('v1:users-list')
    }
    return url_map[api_name]


def get_detail_url(api_name: str, user: AppUser):
    """Get url for user retrieval."""
    kwargs = {'pk': user.pk}
    url_map = {
        'attorney_api': reverse_lazy('v1:attorneys-detail', kwargs=kwargs),
        'client_api': reverse_lazy('v1:clients-detail', kwargs=kwargs),
        'support_api': reverse_lazy('v1:support-detail', kwargs=kwargs),
        'user_api': reverse_lazy('v1:users-detail', kwargs=kwargs)
    }
    return url_map[api_name]


@pytest.fixture
def api_name(request) -> int:
    """Fixture to parametrize api urls."""
    return request.param


@pytest.fixture(scope='function')
def follow_attorney() -> Attorney:
    """Create attorney for follow feature tests."""
    return AttorneyVerifiedFactory()


class TestAuthUser:
    """Test both attorney and clients api for auth users."""
    users_get_list_params = (
        ('client', 'attorney_api',),
        ('attorney', 'attorney_api',),
        ('support', 'attorney_api',),

        ('client', 'client_api',),
        ('attorney', 'client_api',),
        ('support', 'client_api',),

        ('client', 'support_api',),
        ('attorney', 'support_api',),
        ('support', 'support_api',),

        ('client', 'user_api',),
        ('attorney', 'user_api',),
        ('support', 'user_api',),
    )
    users_get_profile_params = (
        ('client', 'attorney_api', 'attorney'),
        ('attorney', 'attorney_api', 'attorney'),
        ('support', 'attorney_api', 'attorney'),

        ('client', 'user_api', 'attorney'),
        ('attorney', 'user_api', 'attorney'),
        ('support', 'user_api', 'attorney'),

        ('client', 'client_api', 'client'),
        ('attorney', 'client_api', 'client'),
        ('support', 'client_api', 'client'),

        ('client', 'user_api', 'client'),
        ('attorney', 'user_api', 'client'),
        ('support', 'user_api', 'client'),

        ('client', 'support_api', 'support'),
        ('attorney', 'support_api', 'support'),
        ('support', 'support_api', 'support'),

        ('client', 'support_api', 'support'),
        ('attorney', 'support_api', 'support'),
        ('support', 'support_api', 'support'),
    )

    @pytest.mark.parametrize(
        argnames='user, api_name',
        argvalues=users_get_list_params,
        indirect=True
    )
    def test_get_list(
        self,
        api_client: APIClient,
        user: AppUser,
        api_name: str,
    ):
        """Test that users can get list of clients, attorneys, support users.
        """
        url = get_list_url(api_name)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == OK

    @pytest.mark.parametrize(
        argnames='user, api_name, other_user',
        argvalues=users_get_profile_params,
        indirect=True
    )
    def test_get_profile(
        self,
        api_client: APIClient,
        user: AppUser,
        api_name: str,
        other_user: AppUser
    ):
        """Test that users can get details of clients, attorneys, support users
        """
        url = get_detail_url(api_name, user=other_user)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == OK

        # Check that only attorney can view it's registration_attachments
        if other_user.is_attorney and api_name != 'user_api':
            assert response.data['registration_attachments'] is None

        # Check that clients can't view each others emails
        if other_user.is_client and user.is_client:
            assert response.data['email'] is None


class TestAttorneyAPI:
    """Test special endpoints for attorney api."""
    users_status_params = (
        ('anonymous', UNAUTHORIZED),
        ('client', NO_CONTENT),
        ('attorney', FORBIDDEN),
    )

    @staticmethod
    def get_follow_url(attorney: Attorney):
        """Get url for following attorney."""
        return reverse_lazy('v1:attorneys-follow', kwargs={'pk': attorney.pk})

    @staticmethod
    def get_unfollow_url(attorney: Attorney):
        """Get url for unfollowing attorney."""
        return reverse_lazy(
            'v1:attorneys-unfollow', kwargs={'pk': attorney.pk}
        )

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=users_status_params,
        indirect=True
    )
    def test_follow_attorney(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code: int,
        follow_attorney: Attorney,
    ):
        """Test that only clients can follow attorney."""
        url = self.get_follow_url(attorney=follow_attorney)

        api_client.force_authenticate(user=user)
        response = api_client.post(url)

        assert response.status_code == status_code

        # Check that client has followed attorney
        if user and user.is_client:
            assert follow_attorney in user.followed_attorneys.all()

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=users_status_params,
        indirect=True
    )
    def test_unfollow_attorney(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code: int,
        follow_attorney: Attorney,
    ):
        """Test that only clients can unfollow attorney."""
        # Make client follow attorney
        if user and user.is_client:
            user.followed_attorneys.add(follow_attorney)

        url = self.get_unfollow_url(attorney=follow_attorney)

        api_client.force_authenticate(user=user)
        response = api_client.post(url)

        assert response.status_code == status_code

        # Check that client has unfollowed attorney
        if user and user.is_client:
            assert follow_attorney not in user.followed_attorneys.all()
