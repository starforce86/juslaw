# Generated by Django 3.0.8 on 2021-09-27 16:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0047_activity_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='matter',
            name='close_date',
            field=models.DateField(blank=True, null=True, verbose_name='Close date'),
        ),
    ]
