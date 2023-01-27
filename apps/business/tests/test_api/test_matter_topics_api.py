from django.urls import reverse_lazy

from rest_framework.test import APIClient

import pytest

from libs.testing.constants import BAD_REQUEST, CREATED, NOT_FOUND, OK

from ....users.models import AppUser
from ... import models
from ...api import serializers


def get_list_url():
    """Get url for matter's topic creation and list retrieval."""
    return reverse_lazy('v1:matter-topic-list')


def get_detail_url(matter_topic: models.MatterTopic):
    """Get url for matter's topic editing and retrieval."""
    return reverse_lazy(
        'v1:matter-topic-detail', kwargs={'pk': matter_topic.pk}
    )


class TestAuthUserAPI:
    """Test matter topic api for auth users.

    Clients can read and create matter topics.
    Attorneys can read and create owned and shared matter topics.
    Support can read and create shared matter topics.

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
    def test_get_list_matter_topics(
        self, api_client: APIClient, user: AppUser,
        matter_topic: models.MatterTopic
    ):
        """Test that users list of matter topics."""
        url = get_list_url()
        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == OK

        topics = models.MatterTopic.objects.available_for_user(user=user)
        assert topics.count() == response.data['count']
        for topic_data in response.data['results']:
            topics.get(pk=topic_data['id'])

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
    def test_retrieve_topic(
        self, api_client: APIClient, user: AppUser,
        matter_topic: models.MatterTopic, matter: models.Matter
    ):
        """Test that users can get details of matter topic."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        url = get_detail_url(matter_topic)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == OK

        models.MatterTopic.objects.available_for_user(
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
    def test_retrieve_foreign_topic(
        self, api_client: APIClient, other_matter_topic: models.MatterTopic,
        user: AppUser
    ):
        """Test that users can't get foreign matter topics."""
        api_client.logout()
        api_client.force_authenticate(user=user)
        url = get_detail_url(other_matter_topic)
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
    def test_create_matter_topic(
        self, api_client: APIClient, user: AppUser,
        matter_topic: models.MatterTopic, matter: models.Matter
    ):
        """Test that users can create matter topic."""
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        data = serializers.MatterTopicSerializer(
            instance=matter_topic
        ).data
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.post(url, data)
        assert response.status_code == CREATED

        # Check that new matter topic appeared in db
        models.MatterTopic.objects.available_for_user(
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
    def test_create_foreign_matter_topic(
        self, api_client: APIClient, other_matter_topic: models.MatterTopic,
        user: AppUser
    ):
        """Test that users can't create topics in foreign matters."""
        api_client.logout()
        api_client.force_authenticate(user=user)
        data = serializers.MatterTopicSerializer(
            instance=other_matter_topic
        ).data
        url = get_list_url()
        response = api_client.post(url, data)
        assert response.status_code == BAD_REQUEST
