from django.db.models import ProtectedError
from django.test import override_settings

import pytest

from apps.business.factories import FullMatterFactory
from apps.business.models import Matter


class TestBaseModel:
    """Tests for `BaseModel` model methods."""

    @override_settings(ENVIRONMENT='development')
    def test_remove(self):
        """Check `remove` BaseModel method on matter instance.

        No protected errors should be raised on matter deletion.

        """
        matter = FullMatterFactory()
        matter.attorney.user.remove()
        with pytest.raises(Matter.DoesNotExist):
            matter.refresh_from_db()

    @override_settings(ENVIRONMENT='production')
    def test_remove_production(self):
        """Check `remove` BaseModel method on matter instance.

        Protected errors should be raised on matter deletion for `production`
        env.

        """
        matter = FullMatterFactory()
        with pytest.raises(ProtectedError):
            matter.attorney.user.delete()
