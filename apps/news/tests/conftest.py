import pytest

from .. import models
from ..factories import NewsFactory


@pytest.fixture(scope='session')
def news(django_db_blocker) -> models.News:
    """Create one news."""
    with django_db_blocker.unblock():
        return NewsFactory()


@pytest.fixture(scope='session')
def news_tag(django_db_blocker) -> models.NewsTag:
    """Create news tag."""
    with django_db_blocker.unblock():
        tag, _ = models.NewsTag.objects.get_or_create(name='test_tag_1')
        return tag


@pytest.fixture(scope='session')
def news_category(django_db_blocker) -> models.NewsCategory:
    """Create news category."""
    with django_db_blocker.unblock():
        category, _ = models.NewsCategory.objects.get_or_create(
            name='test_category_1'
        )
        return category


@pytest.fixture(scope='session')
def news_with_tags(django_db_blocker, news_tag: models.NewsTag) -> models.News:
    """Create one news with tags."""
    with django_db_blocker.unblock():
        news = NewsFactory()
        news.tags.add(news_tag)
        news.tags.add('test_tag_2')
        return news


@pytest.fixture(scope='session')
def news_with_categories(
    django_db_blocker, news_category: models.NewsCategory
) -> models.News:
    """Create one news with categories."""
    with django_db_blocker.unblock():
        news = NewsFactory()
        news.categories.add(news_category)
        news.categories.add('test_category_2')
        return news
