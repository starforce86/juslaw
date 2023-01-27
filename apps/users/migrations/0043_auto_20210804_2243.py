# Generated by Django 3.0.8 on 2021-08-04 22:43

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0042_speciality_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttorneyIndustryContacts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('chat_channel',
                 models.UUIDField(default=uuid.uuid4, editable=False,
                                  unique=True,
                                  verbose_name='Chat channel ID')),
                ('attorney',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                   to='users.Attorney',
                                   verbose_name='Attorney')),
                ('industry_contact',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                   to=settings.AUTH_USER_MODEL,
                                   verbose_name='Industry Contact')),
            ],
        ),
        migrations.AddField(
            model_name='attorney',
            name='industry_contacts',
            field=models.ManyToManyField(
                 related_name='contacted_attorney',
                 through='users.AttorneyIndustryContacts',
                 to=settings.AUTH_USER_MODEL,
                 verbose_name='Industry Contacts'),
        ),
    ]
