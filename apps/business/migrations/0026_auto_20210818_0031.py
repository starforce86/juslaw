# Generated by Django 3.0.8 on 2021-08-18 00:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0025_merge_20210817_1142'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='invoice_id',
            field=models.CharField(max_length=30, null=True, verbose_name='Invoice ID'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='number',
            field=models.CharField(max_length=15, verbose_name='Invoice Number'),
        ),
    ]
