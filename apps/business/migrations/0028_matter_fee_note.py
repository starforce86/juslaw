# Generated by Django 3.0.8 on 2021-08-18 20:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('business', '0027_merge_20210818_1822'),
    ]

    operations = [
        migrations.AddField(
            model_name='matter',
            name='fee_note',
            field=models.TextField(default='', max_length=255,
                                   verbose_name='Fee note'),
        ),
    ]
