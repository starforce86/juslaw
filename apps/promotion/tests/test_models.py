from django.core.exceptions import ValidationError
from django.db import IntegrityError

import arrow
import pytest

from apps.promotion import factories, models
from apps.promotion.models import Event


@pytest.fixture(scope='module')
def event(django_db_blocker, attorney) -> models.Event:
    """Create event for testing."""
    with django_db_blocker.unblock():
        return factories.EventFactory(attorney=attorney)


def test_event_dates_validation_start_equal_to_end(event: Event):
    """Test validation event's start and end fields.

    Check case when start and end are equal.

    """
    date = arrow.now()
    event.start = date.datetime
    event.end = event.start

    with pytest.raises(ValidationError):
        event.clean()

    with pytest.raises(IntegrityError):
        event.save()


def test_event_dates_validation_end_earlier_start(event: Event):
    """Test validation event's start and end fields.

    Check case when end is earlier than start.

    """
    date = arrow.now()

    event.start = date.shift(years=1).datetime

    with pytest.raises(ValidationError):
        event.clean()

    with pytest.raises(IntegrityError):
        event.save()


def test_event_start_date_validation(event):
    """Test validation for event's start field."""

    date = arrow.now()
    event.start = date.shift(days=-1).floor('day').datetime
    event.end = date.ceil('day').datetime
    event.is_all_day = True

    with pytest.raises(ValidationError):
        event.clean()


def test_event_end_date_validation(event):
    """Test validation for event's end field."""

    date = arrow.now()
    event.start = date.shift(days=-1).floor('day').datetime
    event.end = date.shift(days=-1).ceil('day').datetime

    with pytest.raises(ValidationError):
        event.clean()
