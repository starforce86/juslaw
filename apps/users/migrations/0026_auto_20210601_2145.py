# Generated by Django 3.0.8 on 2021-06-01 21:45

import apps.users.models.paralegal_links
import apps.users.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0025_auto_20210528_1755'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParalegalUniversity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=255, unique=True, verbose_name='Title')),
            ],
            options={
                'verbose_name': 'University',
                'verbose_name_plural': 'Universities',
            },
        ),
        migrations.RenameModel(
            old_name='University',
            new_name='AttorneyUniversity',
        ),
        migrations.RenameField(
            model_name='paralegal',
            old_name='fee_kinds',
            new_name='fee_types',
        ),
        migrations.CreateModel(
            name='ParalegalRegistrationAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('attachment', models.FileField(help_text='Extra file attached by paralegal on registration', max_length=255, upload_to=apps.users.models.paralegal_links.upload_registration_attachments_to, verbose_name='Attachment file')),
                ('paralegal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registration_attachments', to='users.Paralegal', verbose_name='Paralegal')),
            ],
            options={
                'verbose_name': "Paralegal's registration attachment",
                'verbose_name_plural': "Paralegal's registration attachments",
            },
        ),
        migrations.CreateModel(
            name='ParalegalEducation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('year', models.IntegerField(validators=[apps.users.validators.validate_activity_year], verbose_name='Year')),
                ('paralegal', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='education', to='users.Paralegal', verbose_name='Paralegal')),
                ('university', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='paralegal_education', to='users.ParalegalUniversity', verbose_name='University')),
            ],
            options={
                'verbose_name': "Paralegal's education",
                'verbose_name_plural': "Paralegals' education",
            },
        ),
    ]
