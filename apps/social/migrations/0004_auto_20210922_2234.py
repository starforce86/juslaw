# Generated by Django 3.0.8 on 2021-09-22 22:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0003_auto_20210825_2038'),
    ]

    operations = [
        migrations.AddField(
            model_name='directchat',
            name='is_archived',
            field=models.BooleanField(default=False, verbose_name='Archived'),
        ),
        migrations.AddField(
            model_name='groupchat',
            name='is_archived',
            field=models.BooleanField(default=False, verbose_name='Archived'),
        ),
    ]
