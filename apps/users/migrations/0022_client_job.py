# Generated by Django 3.0.8 on 2021-05-26 20:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0021_client_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='job',
            field=models.CharField(blank=True, help_text="Client's job title", max_length=128, null=True, verbose_name='Job'),
        ),
    ]
