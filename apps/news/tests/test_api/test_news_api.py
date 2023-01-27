from typing import Union

from django.urls import reverse_lazy

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from ....users.models import AppUser
from ... import models


def get_list_url(model):
    """Get url for news objects list retrieval."""
    mapping = {
        models.News: 'v1:news-list',
        models.NewsCategory: 'v1:news-categories-list',
        models.NewsTag: 'v1:news-tags-list'
    }
    return reverse_lazy(mapping[model])


def get_detail_url(
    obj: Union[models.News, models.NewsCategory, models.NewsTag]
):
    """Get url for news objects retrieval."""
    mapping = {
        models.News: 'v1:news-detail',
        models.NewsCategory: 'v1:news-categories-detail',
        models.NewsTag: 'v1:news-tags-detail'
    }
    return reverse_lazy(mapping[type(obj)], kwargs={'pk': obj.pk})


@pytest.fixture
def news_object(
    request,
    news: models.News,
    news_tag: models.NewsTag,
    news_category: models.NewsCategory,
) -> Union[models.News, models.NewsCategory, models.NewsTag]:
    """Fixture to parametrize news_object fixtures."""
    mapping = {
        'news': news,
        'news_tag': news_tag,
        'news_category': news_category,
    }
    news_object = mapping[request.param]
    return news_object


class TestNewsAPI:
    """Test news api."""

    @pytest.mark.parametrize(
        argnames='user, model',
        argvalues=(
            ('anonymous', models.News),
            ('client', models.News),
            ('attorney', models.News),
            ('anonymous', models.NewsTag),
            ('client', models.NewsTag),
            ('attorney', models.NewsTag),
            ('anonymous', models.NewsCategory),
            ('client', models.NewsCategory),
            ('attorney', models.NewsCategory),
        ),
        indirect=True
    )
    def test_get_list_news_objects(
        self,
        api_client: APIClient,
        user: AppUser,
        model,
    ):
        """Test that users can only get list of news objects."""
        url = get_list_url(model)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Check that everything is correct
        objects = model.objects.all()
        assert objects.count() == response.data['count']
        for data in response.data['results']:
            objects.get(pk=data['id'])

    @pytest.mark.parametrize(
        argnames='user, model, news_object',
        argvalues=(
            ('anonymous', models.News, 'news'),
            ('client', models.News, 'news'),
            ('attorney', models.News, 'news'),
            ('anonymous', models.NewsTag, 'news_tag'),
            ('client', models.NewsTag, 'news_tag'),
            ('attorney', models.NewsTag, 'news_tag'),
            ('anonymous', models.NewsCategory, 'news_category'),
            ('client', models.NewsCategory, 'news_category'),
            ('attorney', models.NewsCategory, 'news_category'),
        ),
        indirect=True
    )
    def test_retrieve_news_object(
        self,
        api_client: APIClient,
        user: AppUser,
        model,
        news_object: Union[models.News, models.NewsCategory, models.NewsTag],
    ):
        """Test that users can get details news objects."""
        url = get_detail_url(news_object)

        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Check correct object was returned
        model.objects.get(pk=response.data['id'])
