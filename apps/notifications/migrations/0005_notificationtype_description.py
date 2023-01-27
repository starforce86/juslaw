# Generated by Django 3.0.8 on 2021-08-16 18:02

from django.db import migrations, models


def update_notification_types(apps, schema_editor):
    notification_types_descriptions = {
        'new_attorney_event': 'New Event',
        'new_attorney_post': 'Forum Activity',
        'matter_status_update': 'Status Update',
        'document_shared_by_attorney': 'File Shared',
        'new_opportunities': 'New Opportunities',
        'new_group_chat': 'New Network',
        'new_message': 'New Message',
        'new_chat': 'New Chat',
        'new_video_call': 'New Video Call',
        'new_post': 'Topics I Follow Activity',
        'new_matter_shared': 'New Matter Shared'
    }
    NotificationType = apps.get_model('notifications', 'NotificationType')

    notification_types = NotificationType.objects.all()

    for notification_type in notification_types:
        notification_type.description = (
            notification_types_descriptions[notification_type.runtime_tag]
        )
        notification_type.save()


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_notificationtype_is_for_other'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationtype',
            name='description',
            field=models.TextField(null=True, verbose_name='Description'),
        ),
        migrations.RunPython(
            code=update_notification_types,
            elidable=False
        ),
    ]
