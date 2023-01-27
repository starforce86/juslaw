# Generated by Django 3.0.8 on 2021-08-16 19:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0023_auto_20210816_1908'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='payment_method',
        ),
        migrations.AddField(
            model_name='invoice',
            name='payment_method',
            field=models.ManyToManyField(related_name='invoices', to='business.PaymentMethods', verbose_name='Payment methods'),
        ),
    ]
