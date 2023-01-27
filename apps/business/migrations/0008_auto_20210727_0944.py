# Generated by Django 3.0.8 on 2021-07-27 09:44

from django.db import migrations
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0007_remove_matter_fee_note'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matter',
            name='status',
            field=django_fsm.FSMField(choices=[('open', 'Open'), ('close', 'Close')], default='open', max_length=15, verbose_name='Status'),
        ),
    ]
