# Generated by Django 3.0.14 on 2021-10-25 18:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0010_auto_20211025_1813'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='messageattachment',
            name='size',
        ),
        migrations.RemoveField(
            model_name='messageattachment',
            name='title',
        ),
    ]