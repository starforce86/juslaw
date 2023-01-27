# Generated by Django 3.0.8 on 2021-08-27 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0038_auto_20210827_1642'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoicelog',
            name='method',
            field=models.CharField(max_length=10, null=True, verbose_name='Method'),
        ),
        migrations.AlterField(
            model_name='invoicelog',
            name='status',
            field=models.CharField(max_length=20, null=True, verbose_name='Status'),
        ),
    ]