# Generated by Django 3.0.8 on 2021-06-07 03:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0026_auto_20210601_2145'),
    ]

    operations = [
        migrations.AddField(
            model_name='paralegal',
            name='role',
            field=models.CharField(blank=True, help_text="Other's special role", max_length=128, null=True, verbose_name='Role'),
        ),
    ]
