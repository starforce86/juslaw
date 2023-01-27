# Generated by Django 3.0.8 on 2021-08-24 20:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('business', '0030_auto_20210820_0136'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeentry',
            name='created_by',
            field=models.ForeignKey(
                editable=False,
                help_text='AppUser created time billing',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='time_entries',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='timeentry',
            name='billing_item',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='time_entries',
                to='business.TimeBilling',
                verbose_name='Billing Item'),
        ),
    ]