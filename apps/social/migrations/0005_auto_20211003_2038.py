# Generated by Django 3.0.8 on 2021-10-03 20:38

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import model_utils.fields


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('social', '0004_auto_20210922_2234'),
    ]

    operations = [
        migrations.CreateModel(
            name='Chats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(
                    default=django.utils.timezone.now, editable=False,
                    verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(
                    default=django.utils.timezone.now, editable=False,
                    verbose_name='modified')),
                ('is_favorite',
                 models.BooleanField(default=False, verbose_name='Favorite')),
                ('is_archived',
                 models.BooleanField(default=False, verbose_name='Archived')),
                ('chat_channel',
                 models.UUIDField(default=uuid.uuid4, editable=False,
                                  unique=True,
                                  verbose_name='Chat channel ID')),
            ],
            options={
                'verbose_name': 'Chat',
                'verbose_name_plural': 'Chats',
            },
        ),
        migrations.CreateModel(
            name='SingleChatParticipants',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(
                    default=django.utils.timezone.now, editable=False,
                    verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(
                    default=django.utils.timezone.now, editable=False,
                    verbose_name='modified')),
                ('is_favorite',
                 models.BooleanField(default=False, verbose_name='Favorite')),
                ('appuser',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                   related_name='single_chat_participants',
                                   to=settings.AUTH_USER_MODEL,
                                   verbose_name='User')),
                ('chat',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                   related_name='single_chat_participants',
                                   to='social.Chats', verbose_name='User')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='chats',
            name='participants',
            field=models.ManyToManyField(
                 related_name='chatss',
                 related_query_name='social_chatss',
                 through='social.SingleChatParticipants',
                 to=settings.AUTH_USER_MODEL,
                 verbose_name='Participants'),
        ),
    ]