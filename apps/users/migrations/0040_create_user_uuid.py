from django.db import migrations
import uuid


def create_uuid(apps, schema_editor):
    users = apps.get_model('users', 'AppUser')
    for user in users.objects.all():
        user.uuid = uuid.uuid4()
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0038_auto_20210723_1758'),
    ]

    operations = [
        migrations.RunPython(create_uuid),
    ]
