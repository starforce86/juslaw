from django.db import migrations


def add_document_matter_notifications(apps, schema_editor):
    NotificationType = apps.get_model('notifications', 'NotificationType')
    new_notifications_data = [
        {
            "runtime_tag": "document_uploaded_to_matter",
            "title": "File uploaded to matter",
            "is_for_attorney": True,
            "is_for_client": False,
            "description": "File uploaded to matter"
        },
    ]
    NotificationType.objects.bulk_create(
        NotificationType(**notification_type_data)
        for notification_type_data in new_notifications_data
    )


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0013_auto_20211104_1349'),
    ]

    operations = [
        migrations.RunPython(
            code=add_document_matter_notifications,
            elidable=False
        ),
    ]
