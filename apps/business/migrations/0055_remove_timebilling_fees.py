# Generated by Django 3.0.14 on 2021-10-21 18:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0054_auto_20211019_1355'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='timebilling',
            name='fees',
        ),
    ]