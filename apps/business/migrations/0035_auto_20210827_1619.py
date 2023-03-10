# Generated by Django 3.0.8 on 2021-08-27 16:19

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0034_auto_20210825_2134'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvoiceLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('logs', models.CharField(help_text='Title which describes current log', max_length=255, null=True, verbose_name='Logs')),
            ],
            options={
                'verbose_name': 'InvoiceLog',
                'verbose_name_plural': 'InvoiceLogs',
            },
        ),
        migrations.RemoveField(
            model_name='invoiceactivity',
            name='invoice',
        ),
        migrations.RemoveField(
            model_name='invoiceactivity',
            name='title',
        ),
        migrations.AddField(
            model_name='invoice',
            name='activities',
            field=models.ManyToManyField(null=True, related_name='invoices', to='business.InvoiceActivity', verbose_name='activities'),
        ),
        migrations.AddField(
            model_name='invoiceactivity',
            name='activity',
            field=models.CharField(help_text='Title which describes current activity', max_length=255, null=True, verbose_name='Activity'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='logs',
            field=models.ManyToManyField(null=True, related_name='invoices', to='business.InvoiceLog', verbose_name='logs'),
        ),
    ]
