from multiprocessing.dummy import active_children
from django.db import migrations


def update_type_activity(apps, schema_editor):
    activities = apps.get_model('business', 'Activity')
    for activity in activities.objects.all():
        if activity.title.startswith('Invoice was sent to client by'):
            activity.type = 'invoice'
        elif activity.title.startswith('Note has been added by'):
            activity.type = 'note'
        elif activity.title.startswith('Message has been added by'):
            activity.type = 'message'
        elif activity.title.startswith('New file has been uploaded to shared'):
            activity.type = 'document'
        activity.save()


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0078_activity_type'),
    ]

    operations = [
        migrations.RunPython(update_type_activity),
    ]
