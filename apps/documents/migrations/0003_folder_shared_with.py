# Generated by Django 3.0.8 on 2021-08-23 15:05

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0002_auto_20210816_1220'),
    ]

    operations = [
        migrations.AddField(
            model_name='folder',
            name='shared_with',
            field=models.ManyToManyField(help_text='Users with which folder is shared', related_name='shared_folder', to=settings.AUTH_USER_MODEL, verbose_name='Shared with'),
        ),
    ]
