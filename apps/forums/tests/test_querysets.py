from datetime import datetime

import arrow
import pytest

from ...users.models import Attorney
from .. import factories, models

date_now = arrow.now()


class TestTopicQuerySet:
    """Test TopicQuerySet."""

    def test_state_search(
        self,
        opportunity_with_keywords: models.Topic,
        opportunity_with_speciality: models.Topic,
        attorney: Attorney,
    ):
        """Test search of topics by client state.

        Search method should return topics where author of first post has same
        state as one of attorney's practice jurisdiction states

        """
        keyword_topics = models.Topic.objects.\
            by_attorney_practice_jurisdictions(
                user=attorney.user
            )
        assert opportunity_with_keywords in keyword_topics
        assert opportunity_with_speciality in keyword_topics

    def test_keywords_search(
        self,
        opportunity_with_keywords: models.Topic,
        attorney: Attorney,
    ):
        """Test search of topics by keywords.

        Search method should return topics with first post or title containing
        keywords that are saved in attorney's profile.

        """
        keyword_topics = models.Topic.objects.\
            by_attorney_specialties_or_keywords(
                user=attorney.user
            )
        assert opportunity_with_keywords in keyword_topics

    def test_speciality_search(
        self,
        opportunity_with_speciality: models.Topic,
        attorney: Attorney,
    ):
        """Test search of topics by speciality.

        Search method should return topics with category matching with
        attorney's specialty.

        """
        speciality_topics = models.Topic.objects.\
            by_attorney_specialties_or_keywords(
                user=attorney.user
            )
        assert opportunity_with_speciality in speciality_topics

    def test_opportunities_search(
        self,
        not_opportunity: models.Topic,
        opportunity_with_keywords: models.Topic,
        opportunity_with_speciality: models.Topic,
        attorney: Attorney,
    ):
        """Check opportunities filter."""
        opportunities = models.Topic.objects.opportunities(
            user=attorney.user
        )
        assert opportunity_with_keywords in opportunities
        assert opportunity_with_speciality in opportunities
        assert not_opportunity not in opportunities

    match_period_data = (
        (
            date_now.shift(days=-1).datetime,
            date_now.shift(days=1).datetime,
            True
        ),
        (date_now.datetime, date_now.shift(days=1).datetime, True),
        # Case when there no opportunities for time period
        (
            date_now.shift(days=2).datetime,
            date_now.shift(days=3).datetime,
            False
        ),
    )

    @pytest.mark.parametrize('start,end,expected', match_period_data)
    def test_opportunities_search_by_time_period(
        self,
        not_opportunity: models.Topic,
        opportunity_with_keywords: models.Topic,
        opportunity_with_speciality: models.Topic,
        attorney: Attorney,
        start: datetime,
        end: datetime,
        expected: bool
    ):
        """Check opportunities filter with time periods."""
        opportunities = models.Topic.objects.opportunities_for_period(
            user=attorney.user,
            period_start=start,
            period_end=end
        )
        assert opportunities.exists() == expected
        if expected:
            assert opportunity_with_keywords in opportunities
            assert opportunity_with_speciality in opportunities
            assert not_opportunity not in opportunities


class TestPostQuerySet:
    """Test PostQuerySet."""

    def test_with_position(self):
        """Test `with_position` method."""
        topic = factories.TopicFactory()
        # set first post manually cause there is no signal on adding topic's
        # `first_post` (all this logic is implemented on API level)
        topic.first_post = factories.PostFactory(topic=topic)
        factories.PostFactory.create_batch(size=2, topic=topic)
        posts = models.Post.objects.filter(topic=topic).with_position()
        assert posts.get(pk=topic.first_post.pk).position == 0
        assert posts.get(pk=topic.last_post.pk).position == posts.count() - 1
