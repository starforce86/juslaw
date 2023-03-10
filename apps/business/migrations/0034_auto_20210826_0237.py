# Generated by Django 3.0.8 on 2021-08-26 02:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0045_auto_20210825_2224'),
        ('business', '0033_auto_20210826_0235'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opportunity',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='opportunities', to='users.Client', verbose_name='Client'),
        ),
    ]
