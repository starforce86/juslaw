# Generated by Django 3.0.14 on 2021-10-19 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0053_proposal_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timebilling',
            name='billing_type',
            field=models.CharField(choices=[('expense', 'Expense'), ('time', 'Time'), ('flat_fee', 'Flat fee')], default='time', max_length=10, verbose_name='Billing Type'),
        ),
    ]
