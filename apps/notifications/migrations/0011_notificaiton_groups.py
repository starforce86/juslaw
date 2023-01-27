from django.db import migrations

groups_data = [
    {
        "title": "chats"
    },
    {
        "title": "matters"
    },
    {
        "title": "forums"
    },
    {
        "title": "contacts"
    },
    {
        "title": "documents"
    },
    {
        "title": "engagements"
    },
    {
        "title": "events"
    },
]
type_group = {
    "chats": [
        "new_group_chat",
        "new_chat_created",
        "new_chat",
        "new_video_call"
    ],
    "matters": [
        "matter_status_update",
        "new_matter_shared",
        "new_matter_referred",
        "new_referral_declined",
        "new_referral_accepted",
        "matter_stage_update",
        "new_message"
    ],
    "forums": [
        "new_post",
        "new_attorney_post"
    ],
    "contacts": [
        "new_opportunities",
        "new_unregistered_contact_shared",
        "new_registered_contact_shared"
    ],
    "documents": [
        "document_shared_by_attorney",
        "document_uploaded"
    ],
    "engagements": [
        "new_proposal",
        "proposal_withdrawn",
        "proposal_accepted",
        "new_post_on_topic",
        "post_deactivated",
        "post_reactivated"
    ],
    "events": ["new_attorney_event"],
}


def add_and_update_notification_groups(apps, schema_editor):
    NotificationType = apps.get_model('notifications', 'NotificationType')
    NotificationGroup = apps.get_model('notifications', 'NotificationGroup')
    NotificationType.objects.all().update(group=None)
    NotificationGroup.objects.all().delete()
    groups = NotificationGroup.objects.bulk_create(
        NotificationGroup(**group_data) for group_data in groups_data
    )
    for group in groups:
        NotificationType.objects.filter(
            runtime_tag__in=type_group[group.title]
        ).update(group=group)


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0010_auto_20211012_1544'),
    ]

    operations = [
        migrations.RunPython(
            code=add_and_update_notification_groups,
            elidable=False
        ),
    ]
