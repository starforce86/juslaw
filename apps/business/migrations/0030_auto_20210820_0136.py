# Generated by Django 3.0.8 on 2021-08-20 01:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0029_auto_20210820_0123'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mattercomment',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='business.MatterPost', verbose_name='Post'),
        ),
    ]
