# Generated by Django 3.0.8 on 2021-07-27 18:53

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import model_utils.fields

import apps.documents.models.resources


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('business', '0007_remove_matter_fee_note'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'created',
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name='created'
                    )
                ),
                (
                    'modified',
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name='modified'
                    )
                ),
                (
                    'mime_type',
                    models.CharField(
                        help_text='Mime type of file',
                        max_length=255,
                        verbose_name='Mime type'
                    )
                ),
                (
                    'file',
                    models.FileField(
                        help_text="Document's file",
                        max_length=255,
                        upload_to=(
                            apps.documents.models.resources.upload_documents_to
                        ),
                        verbose_name='File'
                    )
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='mattertopic',
            name='participants',
            field=models.ManyToManyField(
                related_name='matter_topic',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Participants'
            ),
        ),
        migrations.AddField(
            model_name='mattertopic',
            name='seen',
            field=models.BooleanField(
                default=False,
                help_text='If the matter topic has been read or not',
                verbose_name='Seen'
            ),
        ),
        migrations.AddField(
            model_name='mattertopic',
            name='attachments',
            field=models.ManyToManyField(
                related_name='matter_topic',
                to='business.Attachment',
                verbose_name='Attachments'
            ),
        ),
        migrations.AddField(
            model_name='note',
            name='attachments',
            field=models.ManyToManyField(
                related_name='notes',
                to='business.Attachment',
                verbose_name='Attachments'
            ),
        ),
    ]
