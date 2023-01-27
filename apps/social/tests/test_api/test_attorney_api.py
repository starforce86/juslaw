from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from ....users.models import AppUser
from ... import models
from ...api import serializers
from ...factories import AttorneyPostFactory


def get_list_url():
    """Get url for attorney post creation and list retrieval."""
    return reverse_lazy('v1:attorney_posts-list')


def get_detail_url(attorney_post: models.AttorneyPost):
    """Get url for attorney post editing and retrieval."""
    return reverse_lazy(
        'v1:attorney_posts-detail', kwargs={'pk': attorney_post.pk}
    )


def fix_attorney_post_data(data: dict):
    """Fix attorney post json data."""
    data['image'] = f'http://localhost{data["image"]}'


class TestAuthUserAPI:
    """Test attorney post api for auth users.

    Only attorney have CRUD access, while clients can only view content.

    """

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', status.HTTP_200_OK),
            ('attorney', status.HTTP_200_OK),
        ),
        indirect=True
    )
    def test_get_list_attorney_post(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code: int,
    ):
        """Test that attorney and client can get attorney posts."""
        url = get_list_url()

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status_code, response.data

        attorney_posts = models.AttorneyPost.objects.all()
        assert attorney_posts.count() == response.data['count']
        for attorney_post_data in response.data['results']:
            attorney_posts.get(pk=attorney_post_data['id'])

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', status.HTTP_200_OK),
            ('attorney', status.HTTP_200_OK),
        ),
        indirect=True
    )
    def test_retrieve_attorney_post(
        self,
        api_client: APIClient,
        user: AppUser,
        attorney_post: models.AttorneyPost,
        status_code: int,
    ):
        """Test that attorney and client can get post details."""
        url = get_detail_url(attorney_post)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status_code, response.data
        models.AttorneyPost.objects.all().get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_201_CREATED),
        ),
        indirect=True
    )
    def test_create_attorney_post(
        self,
        api_client: APIClient,
        user: AppUser,
        attorney_post: models.AttorneyPost,
        status_code: int,
    ):
        """Test that attorney can create attorney post, but client can't."""
        attorney_post_json = serializers.AttorneyPostSerializer(
            instance=attorney_post
        ).data
        attorney_post_json['title'] = 'test attorney_post creation'
        url = get_list_url()

        api_client.force_authenticate(user=user)
        fix_attorney_post_data(attorney_post_json)
        response = api_client.post(url, attorney_post_json)

        assert response.status_code == status_code, response.data

        if user.is_attorney:
            # Check that new attorney post appeared in db
            models.AttorneyPost.objects.all().get(pk=response.data['id'])

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', status.HTTP_403_FORBIDDEN),
            ('attorney', status.HTTP_200_OK),
        ),
        indirect=True,
    )
    def test_edit_attorney_post(
        self,
        api_client: APIClient,
        user: AppUser,
        attorney_post: models.AttorneyPost,
        status_code: int,
    ):
        """Test that attorney can edit attorney post, but client can't."""
        attorney_post_json = serializers.AttorneyPostSerializer(
            instance=attorney_post
        ).data
        title = 'test attorney_post editing'
        attorney_post_json['title'] = title
        url = get_detail_url(attorney_post)

        api_client.force_authenticate(user=user)
        fix_attorney_post_data(attorney_post_json)
        response = api_client.put(url, attorney_post_json)

        assert response.status_code == status_code, response.data

        if user.is_attorney:
            # Check that attorney post was updated in db
            attorney_post.refresh_from_db()
            assert attorney_post.title == title

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('client', status.HTTP_403_FORBIDDEN),
            ('other_attorney', status.HTTP_403_FORBIDDEN),
        ),
        indirect=True
    )
    def test_edit_foreign_attorney_post(
        self,
        api_client: APIClient,
        user: AppUser,
        attorney_post: models.AttorneyPost,
        status_code: int
    ):
        """Test that users can't edit attorney post of other user."""
        attorney_post_json = serializers.AttorneyPostSerializer(
            instance=attorney_post
        ).data
        url = get_detail_url(attorney_post)

        api_client.force_authenticate(user=user)
        fix_attorney_post_data(attorney_post_json)
        response = api_client.put(url, attorney_post_json)

        assert response.status_code == status_code, response.data

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('attorney', status.HTTP_204_NO_CONTENT),
        ),
        indirect=True
    )
    def test_post_deletion(
        self, api_client: APIClient, user: AppUser, status_code
    ):
        """Test that user can delete it's own post."""
        attorney_post = AttorneyPostFactory(author=user.attorney)
        url = get_detail_url(attorney_post)

        api_client.force_authenticate(user=user)
        response = api_client.delete(url)
        assert response.status_code == status_code, response.data

    @pytest.mark.parametrize(
        argnames='user,status_code',
        argvalues=(
            ('attorney', status.HTTP_403_FORBIDDEN),
        ),
        indirect=True
    )
    def test_foreign_post_deletion(
        self,
        api_client: APIClient,
        user: AppUser,
        status_code,
        other_attorney_post: models.AttorneyPost,
    ):
        """Test that user can't delete foreign post."""
        url = get_detail_url(other_attorney_post)

        api_client.force_authenticate(user=user)
        response = api_client.delete(url)
        assert response.status_code == status_code, response.data
