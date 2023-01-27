from django.contrib.admin.sites import AdminSite

import pytest
from faker import Faker

from apps.users.models.users import AppUser

from ..admin import AppUserAdmin
from ..factories.users import AppUserWithAvatarFactory

faker = Faker()


@pytest.fixture(scope='module')
def user(django_db_blocker) -> AppUser:
    """Create user for testing"""
    with django_db_blocker.unblock():
        return AppUserWithAvatarFactory(is_superuser=True)


@pytest.fixture(scope='module')
def admin_view():
    """Create admin view for testing"""
    return AppUserAdmin(AppUser, AdminSite())


def test_custom_fields_exist(user, rf, admin_view, settings):
    """Test for existence some custom fields in Admin.

    This custom fields are `_avatar`.

    """
    rf.user = user
    fields = admin_view.get_fields(rf)
    expected_fields = ['avatar_display']

    assert len(expected_fields) == len(set(expected_fields) & set(fields))


def test_avatar_exists(user, admin_view):
    """Test for existence user avatar.

    Checking for returned an HTML `img` tag, that contains URL to avatar.

    """
    expected_html = '<img src="{0}">'.format(user.avatar.url)

    assert admin_view.avatar_display(user) == expected_html


def test_avatar_does_not_exist(user, admin_view):
    """Test for non existence user avatar.

    Should be returned string 'None'.

    """
    user.avatar = None

    assert admin_view.avatar_display(user) == '-'
