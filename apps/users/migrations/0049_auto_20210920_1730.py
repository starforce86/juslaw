# Generated by Django 3.0.8 on 2021-09-20 17:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cities_light', '0008_city_timezone'),
        ('users', '0048_client_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='city',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clients', to='cities_light.City', verbose_name="Client's location(city)"),
        ),
        migrations.AlterField(
            model_name='client',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clients', to='cities_light.Country', verbose_name="Client's location(country)"),
        ),
        migrations.AlterField(
            model_name='client',
            name='state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clients', to='cities_light.Region', verbose_name="Client's location(state)"),
        ),
    ]