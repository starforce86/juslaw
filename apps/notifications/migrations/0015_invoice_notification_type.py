from django.db import migrations


def add_invoice_matter_notifications(apps, schema_editor):
    NotificationType = apps.get_model('notifications', 'NotificationType')
    new_notifications_data = [
        {
            "runtime_tag": "new_invoice",
            "title": "Invoice created to matter",
            "is_for_attorney": True,
            "is_for_client": False,
            "description": "Invoice created to matter"
        },
    ]
    NotificationType.objects.bulk_create(
        NotificationType(**notification_type_data)
        for notification_type_data in new_notifications_data
    )


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0014_document_notification_type'),
    ]

    operations = [
        migrations.RunPython(
            code=add_invoice_matter_notifications,
            elidable=False
        ),
    ]
