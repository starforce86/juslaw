# Generated by Django 3.0.9 on 2020-08-21 02:38
import django.utils.timezone
from django.db import migrations, models

import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial_squashed'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(help_text='Title of event', max_length=255, verbose_name='Title')),
                ('start', models.DateTimeField(verbose_name='Start of event')),
                ('end', models.DateTimeField(verbose_name='End of event')),
                ('is_all_day', models.BooleanField(default=False, help_text='Indicates if event is all day or not', verbose_name='Is event is all day')),
                ('location', models.CharField(blank=True, help_text='Location of event', max_length=255, null=True, verbose_name='Location')),
                ('description', models.TextField(blank=True, help_text='Description of event', null=True, verbose_name='Description')),
                ('attorney', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='events', to='users.Attorney')),
            ],
            options={
                'verbose_name': 'Event',
                'verbose_name_plural': 'Events',
            },
        ),
        migrations.AddConstraint(
            model_name='event',
            constraint=models.CheckConstraint(check=models.Q(start__lt=django.db.models.expressions.F('end')), name='start must be earlier then end'),
        ),
    ]