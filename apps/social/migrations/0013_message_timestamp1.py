# Generated by Django 3.0.14 on 2021-11-02 19:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0012_auto_20211101_1735'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='timestamp1',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Timestamp'),
        ),
    ]