# Generated by Django 3.0.8 on 2021-10-07 11:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0059_auto_20211007_1134'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invite',
            name='job',
        ),
    ]