from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from apps.forums import models
from apps.forums.api import serializers
from apps.forums.factories import PostFactory
from apps.users.models import AppUser, Attorney, Client


@pytest.fixture(scope='module')
def client_post(
    django_db_blocker, client: Client, client_topic: models.Topic
) -> models.Post:
    """Create clients post for testing."""
    with django_db_blocker.unblock():
        return PostFactory(
            topic=client_topic,
            author=client.user,
        )


@pytest.fixture(scope='module')
def attorney_post(
    django_db_blocker, attorney: Attorney, client_topic: models.Topic
) -> models.Post:
    """Create attorneys post for testing."""
    with django_db_blocker.unblock():
        return PostFactory(
            topic=client_topic,
            author=attorney.user,
        )


@pytest.fixture(scope='module')
def other_post(django_db_blocker) -> models.Post:
    """Create post for testing."""
    with django_db_blocker.unblock():
        return PostFactory()


def get_list_url():
    """Get url for post creation and list retrieval."""
    return reverse_lazy('v1:posts-list')


def get_detail_url(post: models.Post):
    """Get url for post editing and retrieval."""
    return reverse_lazy('v1:posts-detail', kwargs={'pk': post.pk})


@pytest.fixture
def post(
    request,
    client_post: models.Post,
    attorney_post: models.Post
) -> models.Post:
    """Fixture to use fixtures in decorator parametrize for Post object."""
    mapping = {
        'client_post': client_post,
        'attorney_post': attorney_post,
    }
    post = mapping[request.param]
    return post


class TestAuthUserAPI:
    """Test posts api for authenticated users."""

    @pytest.mark.parametrize(
        argnames='user, post',
        argvalues=(
            ('client', 'client_post'),
            ('attorney', 'attorney_post')
        ),
        indirect=True
    )
    def test_post_creation(
        self, api_client: APIClient, user: AppUser, post: models.Post
    ):
        """Test that users can create post."""
        post_json = serializers.PostSerializer(instance=post).data

        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.post(url, post_json)
        assert response.status_code == status.HTTP_201_CREATED

        # Check that new post appeared in db
        models.Post.objects.get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user, post',
        argvalues=(
            ('client', 'client_post'),
            ('attorney', 'attorney_post')
        ),
        indirect=True
    )
    def test_post_editing(
        self, api_client: APIClient, user: AppUser, post: models.Post
    ):
        """Test that user can edit it's own post."""
        post_json = serializers.PostSerializer(instance=post).data
        new_text = 'test post editing'
        post_json['text'] = new_text

        url = get_detail_url(post)

        api_client.force_authenticate(user=user)
        response = api_client.put(url, post_json)
        assert response.status_code == status.HTTP_200_OK

        # Check that post data was updated in db
        post.refresh_from_db()
        assert post.text == new_text

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney'
        ),
        indirect=True
    )
    def test_post_deletion(
        self, api_client: APIClient, user: AppUser
    ):
        """Test that user can delete it's own post."""
        post = PostFactory(author=user)
        url = get_detail_url(post)

        api_client.force_authenticate(user=user)
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney'
        ),
        indirect=True
    )
    def test_foreign_post_editing(
        self, api_client: APIClient, user: AppUser, other_post: models.Post
    ):
        """Test that user can't edit foreign post."""
        post_json = serializers.PostSerializer(instance=other_post).data
        new_text = 'test post editing'
        post_json['text'] = new_text

        url = get_detail_url(other_post)

        api_client.force_authenticate(user=user)
        response = api_client.put(url, post_json)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney'
        ),
        indirect=True
    )
    def test_foreign_post_deletion(
        self, api_client: APIClient, user: AppUser, other_post: models.Post
    ):
        """Test that user can't delete foreign post."""
        url = get_detail_url(other_post)

        api_client.force_authenticate(user=user)
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
