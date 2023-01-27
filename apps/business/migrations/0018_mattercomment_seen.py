# Generated by Django 3.0.8 on 2021-08-16 18:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('business', '0017_timebilling_attachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='mattercomment',
            name='seen',
            field=models.BooleanField(
              default=False,
              help_text='If the matter comment has been read or not',
              verbose_name='Seen'),
        ),
    ]
