# Generated by Django 3.0.14 on 2022-03-20 23:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0072_speciality_created_by'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paralegal',
            name='appointment_type',
        ),
        migrations.RemoveField(
            model_name='paralegal',
            name='is_submittable_potential',
        ),
    ]