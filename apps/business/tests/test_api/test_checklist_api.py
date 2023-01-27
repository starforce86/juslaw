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

from ....users.models import AppUser, Attorney
from ... import models
from ...api import serializers
from ...factories import ChecklistEntryFactory


def get_list_url():
    """Get url for checklist entry creation and list retrieval."""
    return reverse_lazy('v1:checklist-list')


def get_detail_url(checklist_entry: models.ChecklistEntry):
    """Get url for checklist entry editing and retrieval."""
    return reverse_lazy(
        'v1:checklist-detail', kwargs={'pk': checklist_entry.pk}
    )


@pytest.fixture(scope="module")
def checklist_entry(
    django_db_blocker, attorney: Attorney
) -> models.ChecklistEntry:
    """Create checklist entry for attorney."""
    with django_db_blocker.unblock():
        return ChecklistEntryFactory(attorney=attorney)


@pytest.fixture(scope="module")
def other_checklist_entry(django_db_blocker) -> models.ChecklistEntry:
    """Create other checklist entry for testing."""
    with django_db_blocker.unblock():
        return ChecklistEntryFactory()


class TestAuthUserAPI:
    """Test checklist api for auth users.

    Attorney have full CRUD access.
    Client doesn't have access to this api.
    Support can only read related to `shared` matter objects.

    """

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', OK),
            # check for users with which matter is shared
            ('support', OK),
            ('shared_attorney', OK),
        ),
        indirect=True
    )
    def test_get_list_checklist(
        self, api_client: APIClient, user: AppUser, status_code: int
    ):
        """Test that all users can get checklist, but clients not."""
        url = get_list_url()
        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status_code

        if status_code != OK:
            return
        checklist_entries = models.ChecklistEntry.objects.filter(
            attorney_id=user.pk
        )
        assert checklist_entries.count() == response.data['count']
        for checklist_data in response.data['results']:
            checklist_entries.get(pk=checklist_data['id'])

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_get_list_checklist_with_matter(
        self, api_client: APIClient, matter: models.Matter, user: AppUser
    ):
        """Test when `matter` is set - checklists of matter's attorney returned
        """
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        api_client.logout()
        api_client.force_authenticate(user=user)

        entry = ChecklistEntryFactory(attorney=matter.attorney)

        url = f'{get_list_url()}?matter={matter.id}'
        response = api_client.get(url)
        assert response.status_code == OK
        assert entry.id in [i['id'] for i in response.data['results']]

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', OK),
            # check shared attorney and support can't get attorney's
            # checklists without `matter`
            ('support', NOT_FOUND),
            ('shared_attorney', NOT_FOUND),
        ),
        indirect=True
    )
    def test_retrieve_checklist_entry(
        self, api_client: APIClient, user: AppUser,
        checklist_entry: models.ChecklistEntry, status_code: int
    ):
        """Test that users can get checklist details, but client can't."""
        url = get_detail_url(checklist_entry)
        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status_code

        if status_code == OK:
            models.ChecklistEntry.objects.filter(attorney_id=user.pk).get(
                pk=response.data['id']
            )

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_retrieve_checklist_with_matter(
        self, api_client: APIClient, user: AppUser,
        matter: models.Matter
    ):
        """Test when `matter` is set - checklists of matter's attorney returned
        """
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        api_client.logout()
        api_client.force_authenticate(user=user)

        entry = ChecklistEntryFactory(attorney=matter.attorney)
        url = f'{get_detail_url(entry)}?matter={matter.id}'
        response = api_client.get(url)
        assert response.status_code == OK
        assert response.data['id'] == entry.id

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', CREATED),
            # shared attorney can create own checklists
            ('shared_attorney', CREATED),
            # support can't create own checklists
            ('support', FORBIDDEN),
        ),
        indirect=True
    )
    def test_create_checklist_entry(
        self, api_client: APIClient, user: AppUser,
        checklist_entry: models.ChecklistEntry, status_code: int
    ):
        """Test attorney can create checklist entry, but client and support not
        """
        checklist_entry_json = serializers.ChecklistEntrySerializer(
            instance=checklist_entry
        ).data
        checklist_entry_json['description'] = 'test checklist_entry creation'
        url = get_list_url()
        api_client.force_authenticate(user=user)
        response = api_client.post(url, checklist_entry_json)

        assert response.status_code == status_code

        if status_code == CREATED:
            # Check that new checklist entry appeared in db
            models.ChecklistEntry.objects.filter(attorney_id=user.pk).get(
                pk=response.data['id']
            )

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', OK),
            # shared attorney can't update foreign checklists
            ('shared_attorney', NOT_FOUND),
            # support can't update own checklists
            ('support', FORBIDDEN),
        ),
        indirect=True
    )
    def test_edit_checklist_entry(
        self, api_client: APIClient, user: AppUser,
        checklist_entry: models.ChecklistEntry, status_code: int
    ):
        """Test that attorney can checklist entry, but client and support can't
        """
        checklist_entry_json = serializers.ChecklistEntrySerializer(
            instance=checklist_entry
        ).data
        description = 'test checklist_entry editing'
        checklist_entry_json['description'] = description
        url = get_detail_url(checklist_entry)
        api_client.force_authenticate(user=user)
        response = api_client.put(url, checklist_entry_json)

        assert response.status_code == status_code

        if status_code == OK:
            # Check that checklist entry was updated in db
            checklist_entry.refresh_from_db()
            assert checklist_entry.description == description

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('attorney', OK),
            # shared attorney and matter
            ('shared_attorney', NOT_FOUND),
            ('support', FORBIDDEN)
        ),
        indirect=True
    )
    def test_edit_checklist_entry_with_matter(
        self, api_client: APIClient,
        matter: models.Matter, user: AppUser, status_code: int
    ):
        """Test users can't edit entry of other user even for shared `matter`.
        """
        api_client.logout()
        api_client.force_authenticate(user=user)

        entry = ChecklistEntryFactory(attorney=matter.attorney)
        checklist_entry_json = serializers.ChecklistEntrySerializer(
            instance=entry
        ).data
        url = f'{get_detail_url(entry)}?matter={matter.id}'
        response = api_client.put(url, checklist_entry_json)
        assert response.status_code == status_code

    def test_edit_foreign_checklist_entry(
        self, auth_attorney_api: APIClient,
        other_checklist_entry: models.ChecklistEntry,
    ):
        """Test that users can't edit checklist entry of other user."""
        checklist_entry_json = serializers.ChecklistEntrySerializer(
            instance=other_checklist_entry
        ).data
        url = get_detail_url(other_checklist_entry)
        response = auth_attorney_api.put(url, checklist_entry_json)
        assert response.status_code == NOT_FOUND

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('client', FORBIDDEN),
            ('attorney', NO_CONTENT),
            # shared attorney can't delete foreign checklists
            ('shared_attorney', NOT_FOUND),
            # shared support can't delete checklists
            ('support', FORBIDDEN),
        ),
        indirect=True
    )
    def test_delete_checklist_entry(
        self, api_client: APIClient, user: AppUser, attorney: Attorney,
        status_code: int
    ):
        """Test attorney can delete checklist entry, clients and support not"""
        url = get_detail_url(ChecklistEntryFactory(attorney=attorney))
        api_client.force_authenticate(user=user)
        response = api_client.delete(url)
        assert response.status_code == status_code

    @pytest.mark.parametrize(
        argnames='user, status_code',
        argvalues=(
            ('attorney', NO_CONTENT),
            # shared attorney and matter
            ('shared_attorney', NOT_FOUND),
            ('support', FORBIDDEN)
        ),
        indirect=True
    )
    def test_delete_checklist_entry_with_matter(
        self, api_client: APIClient, user: AppUser,
        status_code: int, matter: models.Matter
    ):
        """Test users can't delete entry of other user even for shared `matter`
        """
        api_client.logout()
        api_client.force_authenticate(user=user)

        entry = ChecklistEntryFactory(attorney=matter.attorney)
        url = f'{get_detail_url(entry)}?matter={matter.id}'
        response = api_client.delete(url)
        assert response.status_code == status_code

    def test_delete_foreign_checklist_entry(
        self, auth_attorney_api: APIClient,
        other_checklist_entry: models.ChecklistEntry,
    ):
        """Test that users can't delete checklist entry of other user."""
        url = get_detail_url(other_checklist_entry)
        response = auth_attorney_api.delete(url)
        assert response.status_code == NOT_FOUND
