# Generated by Django 3.0.14 on 2022-02-23 20:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0069_client_note'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attorney',
            name='tax_rate',
            field=models.DecimalField(decimal_places=4, default=None, help_text='Tax rate', max_digits=20, null=True, verbose_name='Tax rate'),
        ),
    ]
