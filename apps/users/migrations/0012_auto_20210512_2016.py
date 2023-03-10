# Generated by Django 3.0.8 on 2021-05-12 20:16

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_auto_20210510_1842'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppointmentType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=50, unique=True, verbose_name='Title')),
            ],
            options={
                'verbose_name': 'Appointment Type',
                'verbose_name_plural': 'Appointment Type',
            },
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=50, unique=True, verbose_name='Title')),
            ],
            options={
                'verbose_name': 'Language',
                'verbose_name_plural': 'Language',
            },
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=50, unique=True, verbose_name='Title')),
            ],
            options={
                'verbose_name': 'Payment Method',
                'verbose_name_plural': 'Payment Method',
            },
        ),
        migrations.AddField(
            model_name='attorney',
            name='appointment_type',
            field=models.ManyToManyField(related_name='attorneys', to='users.AppointmentType', verbose_name='AppointmentTypes'),
        ),
        migrations.AddField(
            model_name='attorney',
            name='payment_method',
            field=models.ManyToManyField(related_name='attorneys', to='users.PaymentMethod', verbose_name='PaymentMethods'),
        ),
        migrations.AddField(
            model_name='attorney',
            name='spoken_language',
            field=models.ManyToManyField(related_name='attorneys', to='users.Language', verbose_name='SpokenLanguages'),
        ),
    ]
