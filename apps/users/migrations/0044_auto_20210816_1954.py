# Generated by Django 3.0.8 on 2021-08-16 19:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0043_auto_20210804_2243'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invite',
            name='client_type',
            field=models.CharField(
                choices=[('individual', 'Client'), ('firm', 'Lead')],
                help_text='Type of invitee', max_length=50,
                verbose_name='Type of invitee'),
        ),
        migrations.AlterField(
            model_name='invite',
            name='user_type',
            field=models.CharField(
                choices=[('client', 'Client'), ('attorney', 'Attorney'),
                         ('paralegal', 'Paralegal'), ('lead', 'Lead')],
                default='client', max_length=10,
                verbose_name='Type of invited user'),
        ),
    ]
