# Generated by Django 3.0.14 on 2022-01-12 19:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '0005_post_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='topic',
            name='post_count',
        ),
    ]
