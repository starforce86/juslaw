# Generated by Django 3.0.8 on 2021-05-05 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cities_light', '0008_city_timezone'),
        ('users', '0004_auto_20210427_1900'),
    ]

    operations = [
        migrations.AddField(
            model_name='attorney',
            name='practice_jurisdictions_country',
            field=models.ManyToManyField(help_text='Country(s) or federal jurisdiction attorney are licensed or authorised to practice in', related_name='attorneys', to='cities_light.Country', verbose_name='Practice jurisdictions'),
        ),
    ]
