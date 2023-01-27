# Generated by Django 3.0.14 on 2022-02-09 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0019_chat_notification_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationtype',
            name='is_for_enterprise',
            field=models.BooleanField(default=False, help_text='Is notification type available for enterprise', verbose_name='Is for enterprise'),
        ),
    ]