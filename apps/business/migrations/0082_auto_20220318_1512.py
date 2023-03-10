# Generated by Django 3.0.14 on 2022-03-18 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0081_billingitem_total_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='billingitem',
            name='quantity',
            field=models.PositiveIntegerField(default=None, help_text='Quantity of the item for which expense entry is added', verbose_name='Quantity'),
        ),
        migrations.AlterField(
            model_name='billingitem',
            name='rate',
            field=models.DecimalField(decimal_places=2, default=None, help_text='Unit rate for which expense entry is added', max_digits=10, verbose_name='Rate'),
        ),
    ]
