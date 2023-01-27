# Generated by Django 3.0.8 on 2021-08-12 22:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('business', '0013_auto_20210811_0639'),
    ]

    operations = [
        migrations.AddField(
            model_name='timebilling',
            name='quantity',
            field=models.PositiveIntegerField(
              default=0,
              help_text='Quantity of the item for '
                        'which expense entry is added',
              verbose_name='Quantity'),
        ),
        migrations.AddField(
            model_name='timebilling',
            name='rate',
            field=models.DecimalField(
              decimal_places=2, default=0,
              help_text='Unit rate for which expense entry is added',
              max_digits=10, verbose_name='Rate'),
        ),
    ]
