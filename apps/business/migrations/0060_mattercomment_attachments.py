# Generated by Django 3.0.14 on 2021-11-18 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0059_mattercomment_participants'),
    ]

    operations = [
        migrations.AddField(
            model_name='mattercomment',
            name='attachments',
            field=models.ManyToManyField(related_name='matter_comments', to='business.Attachment', verbose_name='Attachments'),
        ),
    ]