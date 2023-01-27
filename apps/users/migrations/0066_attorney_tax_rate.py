# Generated by Django 3.0.14 on 2022-01-21 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0065_remove_attorney_tax_rate'),
    ]

    operations = [
        migrations.AddField(
            model_name='attorney',
            name='tax_rate',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Tax rate', max_digits=10, verbose_name='Tax rate'),
        ),
    ]
