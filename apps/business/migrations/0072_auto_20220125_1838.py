# Generated by Django 3.0.14 on 2022-01-25 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0071_auto_20220125_1700'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='tax_rate',
            field=models.DecimalField(decimal_places=4, default=0, help_text='Tax rate', max_digits=20, verbose_name='Tax rate'),
        ),
    ]