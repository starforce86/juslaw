import pytest

from ..models import NotificationType

# TODO: we need to update these runtime_tags
#  to make these in accordance with new forums system
#  1) new_attorney_post => new_attorney_comment
#  2) new_post => new_comment

NOTIFICATION_TYPES_DATA = (
    {
        'title': 'New Event',
        'runtime_tag': 'new_attorney_event',
        'is_for_attorney': False,
        'is_for_client': True,
        'is_for_support': False,
    },
    {
        'title': 'Forum Activity',
        'runtime_tag': 'new_attorney_post',
        'is_for_attorney': False,
        'is_for_client': True,
        'is_for_support': False,
    },
    {
        'title': 'Status Update',
        'runtime_tag': 'matter_status_update',
        'is_for_attorney': False,
        'is_for_client': True,
        'is_for_support': False,
    },
    {
        'title': 'File Shared',
        'runtime_tag': 'document_shared_by_attorney',
        'is_for_attorney': False,
        'is_for_client': True,
        'is_for_support': False,
    },
    {
        'title': 'Topics I Follow Activity',
        'runtime_tag': 'new_post',
        'is_for_attorney': True,
        'is_for_client': True,
        'is_for_support': True,
    },
    {
        'title': 'New Message',
        'runtime_tag': 'new_message',
        'is_for_attorney': True,
        'is_for_client': True,
        'is_for_support': False,
    },
    {
        'title': 'New Chat',
        'runtime_tag': 'new_chat',
        'is_for_attorney': True,
        'is_for_client': True,
        'is_for_support': False,
    },
    {
        'title': 'New Video Call',
        'runtime_tag': 'new_video_call',
        'is_for_attorney': True,
        'is_for_client': True,
        'is_for_support': False,
    },
    {
        'title': 'New Opportunities',
        'runtime_tag': 'new_opportunities',
        'is_for_attorney': True,
        'is_for_client': False,
        'is_for_support': False,
    },
    {
        'title': 'New Network',
        'runtime_tag': 'new_group_chat',
        'is_for_attorney': True,
        'is_for_client': False,
        'is_for_support': False,
    },
    {
        'title': 'New Matter Shared',
        'runtime_tag': 'new_matter_shared',
        'is_for_attorney': True,
        'is_for_client': False,
        'is_for_support': True,
    },
)


@pytest.fixture(scope='session', autouse=True)
def generate_notification_type(django_db_blocker):
    """Generate all notification types.

    If we run tests again with reuse-db, we won't have notification_types,
    because migration file creates them and won't run with reuse-db and
    pytest cleans db after each test run. So on next run we won't have
    notification types.

    """
    with django_db_blocker.unblock():
        if NotificationType.objects.exists():
            return
        NotificationType.objects.bulk_create(
            NotificationType(**notification_type_data)
            for notification_type_data in NOTIFICATION_TYPES_DATA
        )
