# Generated by Django 3.0.8 on 2021-10-07 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0058_auto_20211007_1132'),
    ]

    operations = [
        migrations.AddField(
            model_name='invite',
            name='job',
            field=models.CharField(blank=True, help_text="Invitee's job title", max_length=128, null=True, verbose_name='Job'),
        ),
        migrations.AlterField(
            model_name='invite',
            name='client_type',
            field=models.CharField(choices=[('client', 'client'), ('lead', 'lead')], help_text='Type of invitee', max_length=50, verbose_name='Type of invitee'),
        ),
    ]
