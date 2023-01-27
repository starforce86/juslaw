# Generated by Django 3.0.14 on 2022-04-28 06:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0076_auto_20220427_1522'),
        ('business', '0088_auto_20220428_0452'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='enterprise',
            name='firm_locations',
        ),
        migrations.AddField(
            model_name='enterprise',
            name='firm_locations',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.RemoveField(
            model_name='enterprise',
            name='followers',
        ),
        migrations.AddField(
            model_name='enterprise',
            name='followers',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.RemoveField(
            model_name='enterprise',
            name='team_members',
        ),
        migrations.AddField(
            model_name='enterprise',
            name='team_members',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='enterprise',
            name='user',
            field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.PROTECT, related_name='owned_enterprise', to=settings.AUTH_USER_MODEL, verbose_name='Enterprise Admin'),
        ),
    ]