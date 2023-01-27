from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from apps.forums import models
from apps.forums.factories import FollowedTopicFactory, TopicFactory
from apps.users.models import AppUser, Attorney, Client


def get_list_url():
    """Get url for followed topic creation and list retrieval."""
    return reverse_lazy('v1:followed-list')


def get_detail_url(followed_topic: models.FollowedTopic):
    """Get url for followed topic editing and retrieval."""
    return reverse_lazy('v1:followed-detail', kwargs={'pk': followed_topic.pk})


@pytest.fixture(scope='function')
def topic() -> models.Topic:
    """Create topic for testing,"""
    return TopicFactory()


@pytest.fixture(scope='function')
def client_followed_topic(client: Client) -> models.FollowedTopic:
    """Create followed topic for testing."""
    return FollowedTopicFactory(follower=client.user)


@pytest.fixture(scope='function')
def attorney_followed_topic(attorney: Attorney) -> models.FollowedTopic:
    """Create followed topic for testing."""
    return FollowedTopicFactory(follower=attorney.user)


@pytest.fixture
def followed_topic(
    request,
    client_followed_topic: models.FollowedTopic,
    attorney_followed_topic: models.FollowedTopic
) -> models.FollowedTopic:
    """Fixture to use fixtures in decorator parametrize for FollowedTopic."""
    mapping = {
        'client_followed_topic': client_followed_topic,
        'attorney_followed_topic': attorney_followed_topic,
    }
    followed_topic = mapping[request.param]
    return followed_topic


class TestAuthUserAPI:
    """Test followed topics api for authenticated users."""

    @pytest.mark.parametrize(
        argnames='user',
        argvalues=(
            'client',
            'attorney'
        ),
        indirect=True
    )
    def test_follow_topic(
        self, api_client: APIClient, user: AppUser, topic: models.Topic
    ):
        """Test that users can follow topics."""
        followed_json = {
            'topic': topic.pk
        }
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.post(url, followed_json)
        assert response.status_code == status.HTTP_201_CREATED

        # Check that link between topic and user appeared in db
        models.FollowedTopic.objects.get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user, followed_topic',
        argvalues=(
            ('client', 'client_followed_topic'),
            ('attorney', 'attorney_followed_topic')
        ),
        indirect=True
    )
    def test_follow_topic_twice(
        self,
        api_client: APIClient,
        user: AppUser,
        followed_topic: models.FollowedTopic
    ):
        """Test that users can't follow topics twice."""
        followed_json = {
            'topic': followed_topic.topic.pk
        }
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.post(url, followed_json)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        argnames='user, followed_topic',
        argvalues=(
            ('client', 'client_followed_topic'),
            ('attorney', 'attorney_followed_topic')
        ),
        indirect=True
    )
    def test_unfollow_topic(
        self,
        api_client: APIClient,
        user: AppUser,
        followed_topic: models.FollowedTopic
    ):
        """Test that users can unfollow topics."""
        url = get_detail_url(followed_topic)

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
    def test_unfollow_foreign_topic(
        self, api_client: APIClient, user: AppUser,
    ):
        """Test that users can unfollow topics for other users."""
        followed_topic = FollowedTopicFactory()
        url = get_detail_url(followed_topic)

        api_client.force_authenticate(user=user)
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
