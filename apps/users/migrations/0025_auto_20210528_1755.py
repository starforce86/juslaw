# Generated by Django 3.0.8 on 2021-05-28 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0024_paralegal'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paralegal',
            name='is_disciplined',
        ),
        migrations.AddField(
            model_name='paralegal',
            name='is_submittable_potential',
            field=models.BooleanField(default=False, help_text='Sumbit proposals for potential client engagments', verbose_name='Is Submittable Potential'),
        ),
    ]