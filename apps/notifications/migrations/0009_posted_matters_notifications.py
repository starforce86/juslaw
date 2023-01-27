from django.db import migrations


def add_posted_matters_notifications(apps, schema_editor):
    NotificationType = apps.get_model('notifications', 'NotificationType')
    new_notifications_data = [
        {
            "runtime_tag": "post_deactivated",
            "title": "Posted Matter Deactivated",
            "is_for_attorney": True,
            "is_for_client": False,
            "group_id": 2,
            "description": "Posted Matter Deactivated"
        },
        {
            "runtime_tag": "post_reactivated",
            "title": "Posted Matter Reactivated",
            "is_for_attorney": True,
            "is_for_client": False,
            "group_id": 2,
            "description": "Posted Matter Reactivated"
        },
    ]
    NotificationType.objects.bulk_create(
        NotificationType(**notification_type_data)
        for notification_type_data in new_notifications_data
    )


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0008_more_notification_types'),
    ]

    operations = [
        migrations.RunPython(
            code=add_posted_matters_notifications,
            elidable=False
        ),
    ]
