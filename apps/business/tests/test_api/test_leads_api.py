from django.db import IntegrityError
from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import (
    CREATED,
    FORBIDDEN,
    NO_CONTENT,
    NOT_FOUND,
    OK,
)

from ....users.factories import AttorneyFactory
from ....users.models import AppUser, Attorney, Client
from ... import models
from ...api import serializers
from ...factories import LeadFactory, MatterFactory, MatterSharedWithFactory


def get_list_url():
    """Get url for lead creation and list retrieval."""
    return reverse_lazy('v1:leads-list')


def get_detail_url(lead: models.Lead):
    """Get url for lead editing and retrieval."""
    return reverse_lazy('v1:leads-detail', kwargs={'pk': lead.pk})


@pytest.fixture(scope='module')
def other_lead(django_db_blocker) -> models.Lead:
    """Create other lead for testing."""
    with django_db_blocker.unblock():
        return LeadFactory(topic=None)


@pytest.fixture(scope='function')
def lead(
    request,
    attorney_lead: models.Lead,
    client_lead: models.Lead
) -> models.Lead:
    """Fixture to parametrize lead fixtures."""
    mapping = {
        'attorney_lead': attorney_lead,
        'client_lead': client_lead,
    }
    lead = mapping[request.param]
    return lead


@pytest.fixture(scope='function')
def matter(
    django_db_blocker, attorney: Attorney, client: Client
) -> models.Matter:
    """Create matter for testing."""
    with django_db_blocker.unblock():
        return MatterFactory(
            attorney=attorney,
            client=client,
            lead=LeadFactory(attorney=attorney, topic=None)
        )


@pytest.fixture(scope='function')
def shared_attorney(django_db_blocker, matter: models.Matter) -> Attorney:
    """Create attorney for testing."""
    with django_db_blocker.unblock():
        attorney = AttorneyFactory()
        try:
            MatterSharedWithFactory(matter=matter, user_id=attorney.pk)
        except IntegrityError:
            pass
        return attorney


class TestAuthUserAPI:
    """Test leads api for auth users.

    Attorney have full CRUD access.
    Client can only read and create leads.

    """

    @pytest.mark.parametrize(
        argnames='user, other_user',
        argvalues=(
            ('client', 'attorney'),
            ('attorney', 'client')
        ),
        indirect=True
    )
    def test_create_lead(
        self, api_client: APIClient, user: AppUser, other_user: AppUser
    ):
        """Test that users can create lead."""
        lead_json = {
            user.user_type: user.pk,
            other_user.user_type: other_user.pk
        }
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.post(url, lead_json)
        assert response.status_code == CREATED

        # Check that new lead appeared in db
        models.Lead.objects.get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user, lead, status_code',
        argvalues=(
            ('client', 'client_lead', FORBIDDEN),
            ('attorney', 'attorney_lead', OK)
        ),
        indirect=True
    )
    def test_edit_lead(
        self,
        api_client: APIClient,
        user: AppUser,
        lead: models.Lead,
        status_code: int
    ):
        """Test that attorney can edit lead and clients can't."""
        lead_json = serializers.LeadSerializer(instance=lead).data
        lead_json['priority'] = models.Lead.PRIORITY_HIGH
        url = get_detail_url(lead)

        api_client.force_authenticate(user=user)
        response = api_client.put(url, lead_json)
        assert response.status_code == status_code

        if user.is_attorney:
            # Check that data is updated
            lead.refresh_from_db()
            lead.priority = models.Lead.PRIORITY_HIGH

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', NOT_FOUND)
        ),
        indirect=True
    )
    def test_edit_foreign_lead(
        self,
        api_client: APIClient,
        user: AppUser,
        other_lead: models.Lead,
        status_code: int
    ):
        """Test that users can't edit lead of other user."""
        lead_json = serializers.LeadSerializer(instance=other_lead).data
        lead_json['priority'] = models.Lead.PRIORITY_HIGH
        url = get_detail_url(other_lead)

        api_client.force_authenticate(user=user)
        response = api_client.put(url, lead_json)

        assert response.status_code == status_code

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', NO_CONTENT)
        ),
        indirect=True
    )
    def test_delete_lead(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code: int
    ):
        """Test that attorney can delete lead and client can't."""
        url = get_detail_url(
            LeadFactory(**{
                user.user_type: getattr(user, user.user_type),
            })
        )

        api_client.force_authenticate(user=user)
        response = api_client.delete(url)

        assert response.status_code == status_code

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', NOT_FOUND)
        ),
        indirect=True
    )
    def test_delete_foreign_lead(
        self,
        api_client: APIClient,
        user: AppUser,
        other_lead: models.Lead,
        status_code: int
    ):
        """Test that users can't delete lead of other user."""
        url = get_detail_url(other_lead)

        api_client.force_authenticate(user=user)
        response = api_client.delete(url)

        assert response.status_code == status_code
