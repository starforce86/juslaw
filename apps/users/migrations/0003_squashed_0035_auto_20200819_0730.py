# Generated by Django 3.0.9 on 2020-08-21 02:25
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0001_initial_squashed'),
        ('users', '0002_squashed_0029_attorney_sponsored'),
    ]

    operations = [
        migrations.AddField(
            model_name='invite',
            name='matter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invitations', to='business.Matter', verbose_name='Matter'),
        ),
    ]