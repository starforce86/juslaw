from django.db import migrations


def add_attorney_contact_share_notification(apps, schema_editor):
    NotificationType = apps.get_model('notifications', 'NotificationType')
    NotificationGroup = apps.get_model('notifications', 'NotificationGroup')
    group = NotificationGroup.objects.create(
        title='Attorney Notifications'
    )
    NotificationType.objects.create(
        runtime_tag='new_unregistered_contact_shared',
        title='New Unregistered Contact',
        is_for_attorney=True,
        group=group,
        description='New unregistered contact shared'
    )
    NotificationType.objects.create(
        runtime_tag='new_registered_contact_shared',
        title='New Registered Contact',
        is_for_attorney=True,
        group=group,
        description='New registered contact shared'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0005_notificationtype_description'),
    ]

    operations = [
        migrations.RunPython(
            code=add_attorney_contact_share_notification,
            elidable=False
        ),
    ]
