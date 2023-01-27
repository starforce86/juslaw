from operator import itemgetter

from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from apps.forums import models
from apps.forums.api import serializers
from apps.forums.factories import TopicFactory


def get_list_url():
    """Get url for topic creation and list retrieval."""
    return reverse_lazy('v1:topics-list')


def get_detail_url(topic: models.Topic):
    """Get url for topic editing and retrieval."""
    return reverse_lazy('v1:topics-detail', kwargs={'pk': topic.pk})


def get_opportunities_url():
    """Get url for opportunities retrieval."""
    return reverse_lazy('v1:topics-opportunities')


@pytest.fixture(scope='module')
def other_topic(django_db_blocker) -> models.Topic:
    """Create topic for testing,"""
    with django_db_blocker.unblock():
        return TopicFactory()


class TestClientAPI:
    """Test topics api for client.

    We don't test `list` and `retrieve`, we didn't add any special logic for
    this actions.

    """

    def test_create_topic(
        self, auth_client_api: APIClient, client_topic: models.Topic
    ):
        """Test that clients can create topics."""
        topic_json = serializers.TopicSerializer(instance=client_topic).data
        first_post_message = 'test topic creation'
        topic_json['message'] = first_post_message
        url = get_list_url()

        response = auth_client_api.post(url, topic_json)
        assert response.status_code == status.HTTP_201_CREATED

        # Check that new topic appeared in db
        topic = models.Topic.objects.get(pk=response.data['id'])

        # Check that first topic post was created correctly
        first_post = topic.first_post
        last_post = topic.last_post
        assert first_post
        assert last_post

        assert first_post.pk == last_post.pk
        assert first_post.text == first_post_message

    def test_edit_topic(
        self, auth_client_api: APIClient, client_topic: models.Topic
    ):
        """Test that clients can edit topics."""
        topic_json = serializers.TopicSerializer(instance=client_topic).data
        title = 'test topic editing'
        message = 'test topic editing'
        topic_json['title'] = title
        topic_json['message'] = message
        url = get_detail_url(client_topic)

        response = auth_client_api.put(url, topic_json)
        assert response.status_code == status.HTTP_200_OK

        # Test that data in db was updated
        client_topic.refresh_from_db()
        assert client_topic.title == title
        assert client_topic.first_post.text == message

    def test_edit_foreign_topic(
        self, auth_client_api: APIClient, other_topic: models.Topic
    ):
        """Test that clients can't edit foreign topics."""
        topic_json = serializers.TopicSerializer(instance=other_topic).data
        url = get_detail_url(other_topic)

        response = auth_client_api.put(url, topic_json)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_opportunities(self, auth_client_api: APIClient):
        """Test clients doesn't have access to opportunities endpoint."""
        url = get_opportunities_url()

        response = auth_client_api.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAttorneyAPI:
    """Test topics api for attorney.

    We don't test `list` and `retrieve`, we didn't add any special logic for
    this actions.

    """

    def test_create_topic(
        self, auth_attorney_api: APIClient, client_topic: models.Topic
    ):
        """Test that attorneys can't create topics.

        Only clients can create topics.

        """
        topic_json = serializers.TopicSerializer(instance=client_topic).data
        first_post_message = 'test topic creation'
        topic_json['message'] = first_post_message
        url = get_list_url()

        response = auth_attorney_api.post(url, topic_json)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_opportunities(
        self,
        auth_attorney_api: APIClient,
        not_opportunity: models.Topic,
        opportunity_with_keywords: models.Topic,
        opportunity_with_speciality: models.Topic,
    ):
        """Test opportunities endpoint."""
        url = get_opportunities_url()

        response = auth_attorney_api.get(url)
        assert response.status_code == status.HTTP_200_OK

        get_id = itemgetter('id')
        topic_ids = list(map(get_id, response.data['results']))

        # not_opportunity is not opportunity because it's creator(author of
        # first post) is located in attorney's practice jurisdiction
        assert str(not_opportunity.pk) not in topic_ids
        # opportunity_with_keywords is opportunity because it contains
        # attorney's keywords in topic's first post
        assert str(opportunity_with_keywords.pk) not in topic_ids
        # opportunity_with_speciality is opportunity because it's category
        # matches with attorney's specialty
        assert str(opportunity_with_speciality.pk) not in topic_ids
