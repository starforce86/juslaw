from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import BAD_REQUEST, CREATED, NOT_FOUND, OK

from ....users.models import AppUser, Attorney, Client
from ... import models
from ...api import serializers
from ...factories import MatterPostFactory, MatterTopicFactory


def get_list_url():
    """Get url for matter's post creation and list retrieval."""
    return reverse_lazy('v1:matter-post-list')


def get_detail_url(matter_post: models.MatterPost):
    """Get url for matter's post editing and retrieval."""
    return reverse_lazy(
        'v1:matter-post-detail', kwargs={'pk': matter_post.pk}
    )


@pytest.fixture(scope='session')
def matter_topic(
    django_db_blocker, matter: models.Matter
) -> models.MatterTopic:
    """Create matter topic for testing."""
    with django_db_blocker.unblock():
        return MatterTopicFactory(matter=matter)


@pytest.fixture(scope='module')
def client_matter_post(
    django_db_blocker, matter_topic: models.MatterTopic, client: Client
) -> models.MatterPost:
    """Create clients matter post for testing."""
    with django_db_blocker.unblock():
        return MatterPostFactory(topic=matter_topic, author_id=client.pk)


@pytest.fixture(scope='module')
def attorney_matter_post(
    django_db_blocker, matter_topic: models.MatterTopic, attorney: Attorney
) -> models.MatterPost:
    """Create attorney matter post for testing."""
    with django_db_blocker.unblock():
        return MatterPostFactory(
            topic=matter_topic, author_id=attorney.pk
        )


@pytest.fixture(scope='module')
def other_matter_post(django_db_blocker) -> models.MatterPost:
    """Create attorney matter post for testing."""
    with django_db_blocker.unblock():
        return MatterPostFactory()


@pytest.fixture
def matter_post(
    request,
    client_matter_post: models.MatterPost,
    attorney_matter_post: models.MatterPost
) -> models.MatterPost:
    """Fixture to parametrize matter posts fixtures."""
    mapping = {
        'client_matter_post': client_matter_post,
        'attorney_matter_post': attorney_matter_post,
    }
    matter_post = mapping[request.param]
    return matter_post


class TestAuthUserAPI:
    """Test matter post api for auth users.

    Clients can read and create matter posts.
    Attorneys can read and create owned and shared matter posts.
    Support can read and create shared matter posts.

    """

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_get_list_matter_posts(
        self, api_client: APIClient, user: AppUser,
        attorney_matter_post: models.MatterPost, matter: models.Matter
    ):
        """Test that users list of matter posts."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        url = get_list_url()
        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == OK

        posts = models.MatterPost.objects.available_for_user(user=user)
        assert posts.count() == response.data['count']
        for post_data in response.data['results']:
            posts.get(pk=post_data['id'])

        assert attorney_matter_post.id in \
            [i['id'] for i in response.data['results']]

    @pytest.mark.parametrize(
        argnames='user, matter_post',
        argvalues=(
            ('client', 'client_matter_post'),
            ('client', 'attorney_matter_post'),
            ('attorney', 'client_matter_post'),
            ('attorney', 'attorney_matter_post'),

            # check for users with which matter is shared
            ('shared_attorney', 'client_matter_post'),
            ('shared_attorney', 'attorney_matter_post'),
            ('support', 'client_matter_post'),
            ('support', 'attorney_matter_post'),
        ),
        indirect=True
    )
    def test_retrieve_matter_post(
        self, api_client: APIClient, user: AppUser,
        matter_post: models.MatterPost, matter: models.Matter
    ):
        """Test that users can get details of matter post."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        url = get_detail_url(matter_post)
        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == OK

        models.MatterPost.objects.available_for_user(
            user=user
        ).get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney',
            # shared attorney and support
            'shared_attorney',
            'support',
        ),
        indirect=True
    )
    def test_retrieve_foreign_post(
        self, api_client: APIClient, other_matter_post: models.MatterPost,
        user: AppUser
    ):
        """Test that users can't get foreign matter posts."""
        api_client.logout()
        api_client.force_authenticate(user=user)
        url = get_detail_url(other_matter_post)
        response = api_client.get(url)
        assert response.status_code == NOT_FOUND

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_create_matter_post(
        self, api_client: APIClient, user: AppUser,
        matter_topic: models.MatterTopic, matter: models.Matter
    ):
        """Test that users can create matter post."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()
        data = serializers.MatterPostSerializer(
            instance=MatterPostFactory(topic=matter_topic)
        ).data
        url = get_list_url()
        api_client.force_authenticate(user=user)
        response = api_client.post(url, data)
        assert response.status_code == CREATED

        # Check that new matter post appeared in db
        models.MatterPost.objects.available_for_user(
            user=user
        ).get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user,',
        argvalues=(
            'client',
            'attorney',
            # check for users with which matter is shared
            'shared_attorney',
            'support'
        ),
        indirect=True
    )
    def test_create_foreign_matter_post(
        self, api_client: APIClient, other_matter_post: models.MatterPost,
        user: AppUser
    ):
        """Test that users can't create posts in foreign matters."""
        api_client.logout()
        api_client.force_authenticate(user=user)
        data = serializers.MatterPostSerializer(
            instance=other_matter_post
        ).data
        url = get_list_url()
        response = api_client.post(url, data)
        assert response.status_code == BAD_REQUEST
