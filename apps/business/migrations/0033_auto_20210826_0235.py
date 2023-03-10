# Generated by Django 3.0.8 on 2021-08-26 02:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0045_auto_20210825_2224'),
        ('business', '0032_merge_20210824_2244'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='users.Client'),
        ),
        migrations.AlterField(
            model_name='lead',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leads', to='users.Client', verbose_name='Client'),
        ),
        migrations.AlterField(
            model_name='postedmatter',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posted_matters', to='users.Client', verbose_name='Client'),
        ),
        migrations.AlterField(
            model_name='timebilling',
            name='client',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='billed_item', to='users.Client', verbose_name='Client'),
        ),
    ]
