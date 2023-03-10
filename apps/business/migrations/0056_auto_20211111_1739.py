# Generated by Django 3.0.14 on 2021-11-11 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0055_remove_timebilling_fees'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matter',
            name='rate',
            field=models.CharField(help_text='Amount of money taken for a rate type in $', max_length=50, verbose_name='Rate'),
        ),
        migrations.AlterField(
            model_name='proposal',
            name='rate',
            field=models.CharField(max_length=50, verbose_name='rate'),
        ),
    ]
