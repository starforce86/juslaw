from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from ....users.models import AppUser
from ... import factories, models


def get_detail_url() -> str:
    """Get url for retrieving esign profile."""
    return reverse_lazy('v1:current_esign_profile')


class TestESignProfileAPI:
    """Class to test `EnvelopeViewSet`."""

    @pytest.mark.parametrize(
        'user,status_code', [
            (None, status.HTTP_401_UNAUTHORIZED),
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_204_NO_CONTENT),
        ], indirect=True
    )
    def test_delete_current_profile_for_not_existing(
        self, api_client: APIClient, user: AppUser, status_code: int
    ):
        """Test `delete` current envelope profile when it doesn't exist."""
        api_client.force_authenticate(user=user)
        # check that no `esign` profile exists yet
        if user:
            with pytest.raises(models.ESignProfile.DoesNotExist):
                user.esign_profile

        response = api_client.delete(get_detail_url())
        assert response.status_code == status_code
        if user:
            user.refresh_from_db()
            with pytest.raises(models.ESignProfile.DoesNotExist):
                user.esign_profile

    @pytest.mark.parametrize(
        'user,status_code', [
            (None, status.HTTP_401_UNAUTHORIZED),
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_200_OK),
        ], indirect=True
    )
    def test_retrieve_current_profile_for_not_existing(
        self, api_client: APIClient, user: AppUser, status_code: int
    ):
        """Test `retrieve` current envelope profile when it doesn't exist."""
        api_client.force_authenticate(user=user)
        # check that no `esign` profile exists yet
        if user:
            with pytest.raises(models.ESignProfile.DoesNotExist):
                user.esign_profile
        response = api_client.get(get_detail_url())
        assert response.status_code == status_code
        # check that new `esign` profile was created for attorney
        if user and user.is_attorney:
            assert user.esign_profile

    @pytest.mark.parametrize(
        'user,status_code', [
            (None, status.HTTP_401_UNAUTHORIZED),
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_200_OK),
        ], indirect=True
    )
    def test_retrieve_current_profile_for_existing(
        self, api_client: APIClient, user: AppUser, status_code: int
    ):
        """Test `retrieve` current envelope profile when it already exists."""
        api_client.force_authenticate(user=user)
        factories.ESignProfileFactory(user=user) if user else None
        response = api_client.get(get_detail_url())
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        'user,status_code', [
            (None, status.HTTP_401_UNAUTHORIZED),
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_204_NO_CONTENT),
        ], indirect=True
    )
    def test_delete_current_profile_for_existing(
        self, api_client: APIClient, user: AppUser, status_code: int
    ):
        """Test `delete` current envelope profile when it already exists."""
        api_client.force_authenticate(user=user)
        factories.ESignProfileFactory(user=user) if user else None
        response = api_client.delete(get_detail_url())
        assert response.status_code == status_code
        # profile should be deleted for attorney only, cause for client
        # endpoint is not available
        if user and user.is_attorney:
            with pytest.raises(models.ESignProfile.DoesNotExist):
                user.refresh_from_db()
                user.esign_profile
