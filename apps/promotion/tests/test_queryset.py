import arrow

from ...promotion import factories, models


def test_upcoming_filter():
    """Check that upcoming filter for events works properly."""
    date = arrow.now()
    passed_event = factories.EventFactory(
        start=date.shift(hours=-1).datetime,
        end=date.shift(hours=+1).datetime
    )
    event_about_to_happen = factories.EventFactory(
        start=date.shift(hours=+1).datetime,
        end=date.shift(hours=+2).datetime
    )
    all_day_event = factories.EventFactory(
        start=date.datetime,
        is_all_day=True
    )
    upcoming_events = models.Event.objects.upcoming()

    assert passed_event not in upcoming_events
    assert event_about_to_happen in upcoming_events
    assert all_day_event in upcoming_events
