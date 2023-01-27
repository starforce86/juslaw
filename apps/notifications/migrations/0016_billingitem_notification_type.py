from django.db import migrations


def add_billing_item_matter_notifications(apps, schema_editor):
    NotificationType = apps.get_model('notifications', 'NotificationType')
    new_notifications_data = [
        {
            "runtime_tag": "new_billing_item",
            "title": "Billing item created to matter",
            "is_for_attorney": True,
            "is_for_client": False,
            "description": "Billing item created to matter"
        },
    ]
    NotificationType.objects.bulk_create(
        NotificationType(**notification_type_data)
        for notification_type_data in new_notifications_data
    )


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0015_invoice_notification_type'),
    ]

    operations = [
        migrations.RunPython(
            code=add_billing_item_matter_notifications,
            elidable=False
        ),
    ]
