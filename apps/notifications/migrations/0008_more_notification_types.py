from django.db import migrations


def add_new_notifications(apps, schema_editor):
    NotificationType = apps.get_model('notifications', 'NotificationType')
    NotificationGroup = apps.get_model('notifications', 'NotificationGroup')
    group = NotificationGroup.objects.create(
        title='Forums'
    )
    new_notifications_data = [
        {
            "runtime_tag": "new_matter_referred",
            "title": "New Matter Referred",
            "is_for_attorney": True,
            "is_for_client": False,
            "group_id": 2,
            "description": "New Matter Referred"
        },
        {
            "runtime_tag": "new_referral_declined",
            "title": "Referral Declined",
            "is_for_attorney": True,
            "is_for_client": False,
            "group_id": 2,
            "description": "Referral Declined"
        },
        {
            "runtime_tag": "new_referral_accepted",
            "title": "Referral Accepted",
            "is_for_attorney": True,
            "is_for_client": False,
            "group_id": 2,
            "description": "Referral Accepted"
        },
        {
            "runtime_tag": "document_uploaded",
            "title": "File uploaded",
            "is_for_attorney": True,
            "is_for_client": False,
            "description": "File uploaded"
        },
        {
            "runtime_tag": "matter_stage_update",
            "title": "Stage Update",
            "is_for_attorney": False,
            "is_for_client": True,
            "group_id": 2,
            "description": "Stage Update"
        },
        {
            "runtime_tag": "new_proposal",
            "title": "New Proposal Submitted",
            "is_for_attorney": False,
            "is_for_client": True,
            "group_id": 2,
            "description": "New Proposal Submitted"
        },
        {
            "runtime_tag": "proposal_withdrawn",
            "title": "Proposal Withdrawn",
            "is_for_attorney": False,
            "is_for_client": True,
            "group_id": 2,
            "description": "Proposal Withdrawn"
        },
        {
            "runtime_tag": "proposal_accepted",
            "title": "Proposal Accepted",
            "is_for_attorney": True,
            "is_for_client": False,
            "group_id": 2,
            "description": "Proposal Accepted"
        },
        {
            "runtime_tag": "new_post_on_topic",
            "title": "New Post",
            "is_for_attorney": True,
            "is_for_client": True,
            "group": group,
            "description": "New Post"
        },
    ]
    NotificationType.objects.bulk_create(
        NotificationType(**notification_type_data)
        for notification_type_data in new_notifications_data
    )


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0007_auto_20210901_1842'),
    ]

    operations = [
        migrations.RunPython(
            code=add_new_notifications,
            elidable=False
        ),
    ]
