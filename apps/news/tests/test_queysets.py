from apps.news import models


class TestNewsQuerySets:
    """Test NewsQuerySets for news model."""

    def test_filler_by_tags(self, news_with_tags: models.News):
        """Test filler_by_tags method."""
        news = models.News.objects.filler_by_tags(
            tags=['test_tag_1', 'test_tag_2']
        )

        assert news.exists()
        assert news_with_tags in news
        # Check that there no duplicates
        assert news.filter(pk=news_with_tags.pk).count() == 1

    def test_filler_by_categories(self, news_with_categories: models.News):
        """Test filler_by_categories method."""
        news = models.News.objects.filler_by_categories(
            categories=['test_category_1', 'test_category_2']
        )

        assert news.exists()
        assert news_with_categories in news
        # Check that there no duplicates
        assert news.filter(pk=news_with_categories.pk).count() == 1
