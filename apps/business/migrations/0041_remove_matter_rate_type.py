# Generated by Django 3.0.8 on 2021-09-02 17:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0040_merge_20210902_1747'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='matter',
            name='rate_type',
        ),
    ]