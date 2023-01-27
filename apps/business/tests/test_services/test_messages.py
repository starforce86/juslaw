import pytest

from ... import factories, models
from ...services import messages as services


@pytest.fixture(scope="module")
def topic_with_posts(django_db_blocker, matter) -> models.MatterTopic:
    """Create MatterTopic object with some posts."""
    with django_db_blocker.unblock():
        topic = factories.MatterTopicFactory(matter=matter)
        factories.MatterPostFactory.create_batch(topic=topic, size=2)
        return topic


@pytest.mark.parametrize('increase_by', [3, None, 0])
def test_set_matter_topic_post_count(increase_by, topic_with_posts):
    """Test for `get_invoice_period_str_representation` method.

    Check that method correctly saves MatterTopic `posts_count`.

    """
    services.set_matter_topic_post_count(topic_with_posts, increase_by)
    topic_with_posts.refresh_from_db()
    expected_count = topic_with_posts.posts.count() + \
        (increase_by if increase_by is not None else 0)
    assert topic_with_posts.post_count == expected_count
    topic_with_posts.title = '123'
    topic_with_posts.save()


def test_set_matter_topic_last_post_w_last_post(topic_with_posts):
    """Test for `set_matter_topic_last_post` method.

    Check that when `last_post` is set in method call -> it will be used as
    topic's last post.

    """
    # use not last, but first post
    post = topic_with_posts.posts.order_by('created').first()
    services.set_matter_topic_last_post(topic_with_posts, post)
    topic_with_posts.refresh_from_db()
    print(topic_with_posts.title)
    assert topic_with_posts.last_post == post
    topic_with_posts.save()


def test_set_matter_topic_last_post(topic_with_posts):
    """Test for `set_matter_topic_last_post` method for different cases.

    Check that when `last_post` is not set in method call -> as topic last
    post will be taken the last `created` post.

    """
    # use last post
    post = topic_with_posts.posts.order_by('-created').first()
    services.set_matter_topic_last_post(topic_with_posts)
    topic_with_posts.refresh_from_db()
    assert topic_with_posts.last_post == post
