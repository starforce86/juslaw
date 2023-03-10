# Generated by Django 3.0.8 on 2021-09-24 19:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0052_auto_20210922_1557'),
    ]

    operations = [
        migrations.AddField(
            model_name='enterprise',
            name='contacted_clients',
            field=models.ManyToManyField(help_text='List of contacted client',
                                         related_name='enterprise',
                                         to='users.Client',
                                         verbose_name='Contacted Client'),
        ),
        migrations.AddField(
            model_name='paralegal',
            name='contacted_clients',
            field=models.ManyToManyField(help_text='List of contacted client',
                                         related_name='paralegal',
                                         to='users.Client',
                                         verbose_name='Contacted Client'),
        ),
    ]
