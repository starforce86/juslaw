from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0007_auto_20210927_1522'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='transaction_id',
            field=models.CharField(blank=True, help_text='Transaction ID',
                                   max_length=128, null=True, verbose_name='Transaction ID'),
        ),
    ]
