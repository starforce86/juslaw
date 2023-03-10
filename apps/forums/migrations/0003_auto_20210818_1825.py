# Generated by Django 3.0.8 on 2021-08-18 18:25

import django.utils.timezone
from django.db import migrations, models

import model_utils.fields

from apps.forums.management.commands.set_up_categories import categories_data


def set_up_forum_topics(apps, schema_editor):
    ForumPracticeAreas = apps.get_model('forums', 'ForumPracticeAreas')
    ForumPracticeAreas.objects.bulk_create(
        ForumPracticeAreas(
            title=category_data['title']
        ) for category_data in categories_data
    )


class Migration(migrations.Migration):
    dependencies = [
        ('forums', '0002_auto_20210803_1231'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForumPracticeAreas',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(
                    default=django.utils.timezone.now, editable=False,
                    verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(
                    default=django.utils.timezone.now, editable=False,
                    verbose_name='modified')),
                ('title', models.CharField(max_length=100, unique=True,
                                           verbose_name='Title')),
                ('description', models.TextField(blank=True, null=True,
                                                 verbose_name='Description')),
            ],
            options={
                'verbose_name': 'Practice area',
                'verbose_name_plural': 'Practice areas',
            },
        ),
        migrations.RunPython(
            code=set_up_forum_topics,
            elidable=False
        ),
        migrations.AlterField(
            model_name='topic',
            name='practice_area',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='forum_topics',
                to='forums.ForumPracticeAreas',
                verbose_name='Related practice area'),
        ),
    ]
