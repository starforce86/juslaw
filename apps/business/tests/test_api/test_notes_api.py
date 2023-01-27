from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import (
    BAD_REQUEST,
    CREATED,
    NO_CONTENT,
    NOT_FOUND,
    OK,
)

from ....users.models import AppUser, Attorney, Client, Support
from ... import models
from ...api import serializers
from ...factories import NoteFactory


def get_list_url():
    """Get url for note creation and list retrieval."""
    return reverse_lazy('v1:notes-list')


def get_detail_url(note: models.Note):
    """Get url for note editing and retrieval."""
    return reverse_lazy('v1:notes-detail', kwargs={'pk': note.pk})


@pytest.fixture(scope="module")
def attorney_note(
    django_db_blocker, attorney: Attorney, matter: models.Matter
) -> models.Note:
    """Create note for attorney."""
    with django_db_blocker.unblock():
        return NoteFactory(matter=matter, created_by_id=attorney.pk)


@pytest.fixture(scope="module")
def client_note(
    django_db_blocker, client: Client, matter: models.Matter
) -> models.Note:
    """Create note for client."""
    with django_db_blocker.unblock():
        return NoteFactory(matter=matter, created_by_id=client.pk)


@pytest.fixture(scope="module")
def support_note(
    django_db_blocker, support: Support, matter: models.Matter
) -> models.Note:
    """Create note for support."""
    with django_db_blocker.unblock():
        return NoteFactory(matter=matter, created_by_id=support.pk)


@pytest.fixture(scope="module")
def shared_attorney_note(
    django_db_blocker, shared_attorney: Attorney, matter: models.Matter
) -> models.Note:
    """Create note for support."""
    with django_db_blocker.unblock():
        return NoteFactory(matter=matter, created_by_id=shared_attorney.pk)


@pytest.fixture(scope="module")
def other_note(django_db_blocker) -> models.Note:
    """Create other note for testing."""
    with django_db_blocker.unblock():
        return NoteFactory()


@pytest.fixture
def note(
    request, attorney_note: models.Note, client_note: models.Note,
    support_note: models.Note, shared_attorney_note: models.Note,
) -> models.Note:
    """Fixture to parametrize notes fixtures."""
    mapping = {
        'attorney_note': attorney_note,
        'client_note': client_note,
        'support_note': support_note,
        'shared_attorney_note': shared_attorney_note,
    }
    note = mapping[request.param]
    return note


class TestAuthUserAPI:
    """Test note api for auth users.

    All client, attorney, support users have full CRUD access over matters'
    notes, but only for those that were created by them (Attorney can only see
    it's notes, Client can only see it's notes, Support can only see it's
    notes).

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
    def test_get_list_notes(
        self, api_client: APIClient, user: AppUser, attorney_note: models.Note,
        client_note: models.Note, support_note: models.Note,
        shared_attorney_note: models.Note
    ):
        """Test that users can only get details of it's created note."""
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == OK

        notes = models.Note.objects.available_for_user(user=user)
        assert notes.count() == response.data['count']
        for note_data in response.data['results']:
            notes.get(pk=note_data['id'])

    @pytest.mark.parametrize(
        argnames='user, note, status_code',
        argvalues=(
            ('client', 'client_note', OK),
            ('client', 'attorney_note', NOT_FOUND),
            ('client', 'support_note', NOT_FOUND),
            ('client', 'shared_attorney_note', NOT_FOUND),

            ('attorney', 'client_note', NOT_FOUND),
            ('attorney', 'attorney_note', OK),
            ('attorney', 'support_note', NOT_FOUND),
            ('attorney', 'shared_attorney_note', NOT_FOUND),

            # shared attorney and support

            ('support', 'client_note', NOT_FOUND),
            ('support', 'attorney_note', NOT_FOUND),
            ('support', 'support_note', OK),
            ('support', 'shared_attorney_note', NOT_FOUND),

            ('shared_attorney', 'client_note', NOT_FOUND),
            ('shared_attorney', 'attorney_note', NOT_FOUND),
            ('shared_attorney', 'support_note', NOT_FOUND),
            ('shared_attorney', 'shared_attorney_note', OK),

        ),
        indirect=True
    )
    def test_retrieve_note(
        self, api_client: APIClient, user: AppUser, note: models.Note,
        status_code: int, matter: models.Matter
    ):
        """Test that users can only get details of it's created note."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        url = get_detail_url(note)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == status_code

        if response.status_code == OK:
            models.Note.objects.available_for_user(
                user=user
            ).get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user, note',
        argvalues=(
            ('client', 'client_note'),
            ('attorney', 'attorney_note'),
            # shared attorney and support
            ('support', 'support_note'),
            ('shared_attorney', 'shared_attorney_note'),
        ),
        indirect=True
    )
    def test_create_note(
        self, api_client: APIClient, user: AppUser, note: models.Note,
        matter: models.Matter
    ):
        """Test that users can create note."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        note_json = serializers.NoteSerializer(instance=note).data
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.post(url, note_json)
        assert response.status_code == CREATED

        # Check that new note appeared in db
        models.Note.objects.get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user, note',
        argvalues=(
            ('client', 'client_note'),
            ('attorney', 'attorney_note'),
            # shared attorney and support
            ('support', 'support_note'),
            ('shared_attorney', 'shared_attorney_note'),
        ),
        indirect=True
    )
    def test_create_note_foreign_matter(
        self, api_client: APIClient, another_matter: models.Matter,
        note: models.Note, user: AppUser
    ):
        """Test that users can't create notes in foreign matters."""
        api_client.logout()
        api_client.force_authenticate(user=user)

        note_json = serializers.NoteSerializer(instance=note).data
        note_json['matter'] = another_matter.id
        response = api_client.post(get_list_url(), note_json)
        assert response.status_code == BAD_REQUEST

    @pytest.mark.parametrize(
        argnames='user, note',
        argvalues=(
            ('client', 'client_note'),
            ('attorney', 'attorney_note'),
            # shared attorney and support
            ('support', 'support_note'),
            ('shared_attorney', 'shared_attorney_note'),
        ),
        indirect=True
    )
    def test_edit_note(
        self, api_client: APIClient, user: AppUser, note: models.Note,
        matter: models.Matter
    ):
        """Test that users can edit note."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        note_json = serializers.NoteSerializer(instance=note).data
        text = 'test note editing'
        note_json['text'] = text
        url = get_detail_url(note)

        api_client.force_authenticate(user=user)
        response = api_client.put(url, note_json)
        assert response.status_code == OK

        # Check that note was updated in db
        note.refresh_from_db()
        assert note.text == text

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney',
            # shared attorney and support
            'support',
            'shared_attorney',
        ),
        indirect=True
    )
    def test_edit_foreign_note(
        self, api_client: APIClient, user: AppUser, other_note: models.Note
    ):
        """Test that users can't edit note of other user."""
        note_json = serializers.NoteSerializer(instance=other_note).data
        url = get_detail_url(other_note)

        api_client.force_authenticate(user=user)
        response = api_client.put(url, note_json)
        assert response.status_code == NOT_FOUND

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney',
            # shared attorney and support
            'support',
            'shared_attorney',
        ),
        indirect=True
    )
    def test_delete_note(
        self, api_client: APIClient, user: AppUser, matter: models.Matter
    ):
        """Test that users can delete note."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        url = get_detail_url(NoteFactory(created_by=user, matter=matter))

        api_client.force_authenticate(user=user)
        response = api_client.delete(url)
        assert response.status_code == NO_CONTENT

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney',
            # shared attorney and support
            'support',
            'shared_attorney',
        ),
        indirect=True
    )
    def test_delete_foreign_note(
        self, api_client: APIClient, user: AppUser, other_note: models.Note
    ):
        """Test that users can't delete note of other user."""
        url = get_detail_url(other_note)

        api_client.force_authenticate(user=user)
        response = api_client.delete(url)
        assert response.status_code == NOT_FOUND
