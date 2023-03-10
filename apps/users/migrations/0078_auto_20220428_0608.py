# Generated by Django 3.0.14 on 2022-04-28 06:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0077_auto_20220428_0603'),
    ]

    operations = [
        migrations.AddField(
            model_name='enterprise',
            name='id',
            field=models.AutoField(auto_created=True,
                                   primary_key=True, serialize=True,
                                   verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='attorney',
            name='enterprise',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attorneys', to='users.Enterprise', verbose_name='Enterprise'),
        ),
        migrations.AddField(
            model_name='paralegal',
            name='enterprise',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paralegals', to='users.Enterprise', verbose_name='Enterprise'),
        ),
        migrations.RemoveField(
            model_name='enterprise',
            name='firm_locations',
        ),
        migrations.AddField(
            model_name='enterprise',
            name='firm_locations',
            field=models.ManyToManyField(help_text="Country, State(s), Address(s), City(s), Zipcode of enterprise's Firm", related_name='enterprise', to='users.FirmLocation', verbose_name='Firm Location'),
        ),
        migrations.RemoveField(
            model_name='enterprise',
            name='followers',
        ),
        migrations.AddField(
            model_name='enterprise',
            name='followers',
            field=models.ManyToManyField(related_name='followed_enterprise', to=settings.AUTH_USER_MODEL, verbose_name='Followers'),
        ),
        migrations.RemoveField(
            model_name='enterprise',
            name='team_members',
        ),
        migrations.AddField(
            model_name='enterprise',
            name='team_members',
            field=models.ManyToManyField(help_text='Email, User type of enterprise members', related_name='enterprise', to='users.Member', verbose_name='Team Members'),
        ),
    ]
