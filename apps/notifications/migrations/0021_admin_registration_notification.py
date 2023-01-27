from django.db import migrations


def add_admin_registration_notifications(apps, schema_editor):
    NotificationType = apps.get_model('notifications', 'NotificationType')
    new_notifications_data = [
        {
            "runtime_tag": "new_user_registered",
            "title": "A new user is registered",
            "is_for_attorney": True,
            "is_for_enterprise": True,
            "is_for_paralegal": True,
            "is_for_client": False,
            "description": "A new user is registered",
        },
    ]
    NotificationType.objects.bulk_create(
        NotificationType(**notification_type_data)
        for notification_type_data in new_notifications_data
    )


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0020_notificationtype_is_for_enterprise'),
    ]

    operations = [
        migrations.RunPython(
            code=add_admin_registration_notifications,
            elidable=False
        ),
    ]
