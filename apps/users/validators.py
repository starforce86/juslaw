from datetime import datetime

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_activity_year(year: int):
    """Validate year of person's activity.

    For example graduation year or year of employment.

    Rules:
        Your graduation year can't be from future. For example
        current year is 2019, but your graduation year is 2020.
        Your year of employment can't be from distant past
        (more than 100 years ago).

    """
    cur_year = datetime.now().year
    if year > cur_year or year < cur_year - 100:
        raise ValidationError(
            _('Please, enter valid year.')
        )


def validate_experience_years(years: int):
    """Validate the amount of experience years.

    Rules:
        It's impossible for a human to have more than 100 years of experience.

    """
    if years > 100:
        raise ValidationError(
            _('Please, enter valid amount of experience years.')
        )
