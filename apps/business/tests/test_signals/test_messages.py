from unittest.mock import MagicMock, patch

from ... import factories, models


@patch('apps.business.signals.messages.new_message')
def test_new_message_signal(
    signal_mock: MagicMock,
    matter_topic: models.MatterTopic
):
    """Test that `new_message` signal works."""
    instance = factories.MatterPostFactory(topic=matter_topic)
    signal_mock.send.assert_called_with(
        sender=instance.__class__, instance=instance
    )
