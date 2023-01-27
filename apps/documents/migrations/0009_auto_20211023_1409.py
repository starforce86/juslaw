# Generated by Django 3.0.14 on 2021-10-23 14:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0008_document_transaction_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='document', related_query_name='documents_document', to=settings.AUTH_USER_MODEL, verbose_name='client'),
        ),
        migrations.AddField(
            model_name='folder',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='folder', related_query_name='documents_folder', to=settings.AUTH_USER_MODEL, verbose_name='client'),
        ),
    ]
