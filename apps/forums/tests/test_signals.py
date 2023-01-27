from unittest.mock import MagicMock, patch

from ...users.models import Attorney
from ..factories import PostFactory
from ..models import Topic


@patch('apps.forums.signals.new_post_in_topic')
@patch('apps.forums.signals.new_post_in_topic_by_attorney')
def test_new_post_in_topic_by_attorney_signal(
    signal_mock_attorney_case: MagicMock,
    signal_mock: MagicMock,
    attorney: Attorney,
):
    """Test that `new_post_in_topic_by_attorney` signal works."""
    instance = PostFactory(author=attorney.user)
    signal_mock.send.assert_called_with(
        sender=instance.__class__, instance=instance
    )
    signal_mock_attorney_case.send.assert_called_with(
        sender=instance.__class__, instance=instance
    )


@patch('apps.forums.signals.new_post_in_topic')
@patch('apps.forums.signals.new_post_in_topic_by_attorney')
def test_new_post_in_topic_signal(
    signal_mock_attorney_case: MagicMock,
    signal_mock: MagicMock,
    followed_topic: Topic,
):
    """Test that `new_post_in_topic` signal works."""
    instance = PostFactory(topic=followed_topic)
    signal_mock.send.assert_called_with(
        sender=instance.__class__, instance=instance
    )
    signal_mock_attorney_case.send.assert_not_called()
