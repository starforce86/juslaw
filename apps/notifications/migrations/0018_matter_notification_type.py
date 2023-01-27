from django.db import migrations


def add_matter_notifications(apps, schema_editor):
    NotificationType = apps.get_model('notifications', 'NotificationType')
    new_notifications_data = [
        {
            "runtime_tag": "new_matter",
            "title": "A new matter is created",
            "is_for_attorney": True,
            "is_for_client": False,
            "description": "A new matter is created",
        },
    ]
    NotificationType.objects.bulk_create(
        NotificationType(**notification_type_data)
        for notification_type_data in new_notifications_data
    )


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0017_notificationdispatch_sender'),
    ]

    operations = [
        migrations.RunPython(
            code=add_matter_notifications,
            elidable=False
        ),
    ]
