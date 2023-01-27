from django.db import migrations


def add_new_chat_message_notifications(apps, schema_editor):
    NotificationType = apps.get_model('notifications', 'NotificationType')
    new_notifications_data = [
        {
            "runtime_tag": "new_chat_message",
            "title": "A new message is sent",
            "is_for_attorney": True,
            "is_for_client": True,
            "description": "A new message is sent",
        },
    ]
    NotificationType.objects.bulk_create(
        NotificationType(**notification_type_data)
        for notification_type_data in new_notifications_data
    )


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0018_matter_notification_type'),
    ]

    operations = [
        migrations.RunPython(
            code=add_new_chat_message_notifications,
            elidable=False
        ),
    ]
