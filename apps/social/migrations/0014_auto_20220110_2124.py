# Generated by Django 3.0.14 on 2022-01-10 21:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0013_message_timestamp1'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chats',
            name='title',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Title'),
        ),
    ]