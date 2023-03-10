# Generated by Django 3.0.8 on 2021-08-03 12:31

import apps.forums.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0041_auto_20210803_1231'),
        ('forums', '0001_initial_squashed'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('text', models.TextField(verbose_name='Text of the comment')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='comments', to=settings.AUTH_USER_MODEL, verbose_name='Author')),
            ],
            options={
                'verbose_name': 'Comment',
                'verbose_name_plural': 'Comments',
            },
        ),
        migrations.CreateModel(
            name='FollowedPost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('unread_comments_count', models.PositiveIntegerField(default=0, verbose_name='Unread comments in post')),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followed_topics', to=settings.AUTH_USER_MODEL, verbose_name='Follower')),
                ('last_read_comment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='last_read_comment', to='forums.Comment', verbose_name='Last read comment')),
            ],
            options={
                'verbose_name': 'Follower of the Post',
                'verbose_name_plural': 'Followers of Posts',
            },
        ),
        migrations.AlterUniqueTogether(
            name='followedtopic',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='followedtopic',
            name='follower',
        ),
        migrations.RemoveField(
            model_name='followedtopic',
            name='last_read_post',
        ),
        migrations.RemoveField(
            model_name='followedtopic',
            name='topic',
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'verbose_name': 'Posts', 'verbose_name_plural': 'Posts'},
        ),
        migrations.RemoveField(
            model_name='post',
            name='author',
        ),
        migrations.RemoveField(
            model_name='post',
            name='text',
        ),
        migrations.RemoveField(
            model_name='topic',
            name='category',
        ),
        migrations.RemoveField(
            model_name='topic',
            name='first_post',
        ),
        migrations.RemoveField(
            model_name='topic',
            name='last_post',
        ),
        migrations.RemoveField(
            model_name='userstats',
            name='post_count',
        ),
        migrations.AddField(
            model_name='post',
            name='comment_count',
            field=models.PositiveIntegerField(default=0, verbose_name='Number of comments on post'),
        ),
        migrations.AddField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=255, null=True, verbose_name='Title'),
        ),
        migrations.AddField(
            model_name='topic',
            name='comment_count',
            field=models.PositiveIntegerField(default=0, verbose_name='Number of comments in topic'),
        ),
        migrations.AddField(
            model_name='topic',
            name='description',
            field=models.TextField(null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='topic',
            name='featured',
            field=models.BooleanField(default=True, verbose_name='Show on main page.'),
        ),
        migrations.AddField(
            model_name='topic',
            name='followers',
            field=models.ManyToManyField(related_name='topics', to=settings.AUTH_USER_MODEL, verbose_name='Followers'),
        ),
        migrations.AddField(
            model_name='topic',
            name='icon',
            field=models.ImageField(blank=True, null=True, upload_to=apps.forums.models.upload_topic_icons_to, verbose_name='Icon link'),
        ),
        migrations.AddField(
            model_name='topic',
            name='practice_area',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='forum_topics', to='users.Speciality', verbose_name='Related practice area'),
        ),
        migrations.AddField(
            model_name='userstats',
            name='comment_count',
            field=models.PositiveIntegerField(default=0, verbose_name='Number of user comments on forum'),
        ),
        migrations.AlterField(
            model_name='post',
            name='topic',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='forums.Topic', verbose_name='Topic'),
        ),
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.DeleteModel(
            name='FollowedTopic',
        ),
        migrations.AddField(
            model_name='followedpost',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='forums.Post', verbose_name='Post'),
        ),
        migrations.AddField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='comments', to='forums.Post', verbose_name='Post'),
        ),
        migrations.AddField(
            model_name='post',
            name='first_comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='first_post_on_post', to='forums.Comment', verbose_name='First comment on post'),
        ),
        migrations.AddField(
            model_name='post',
            name='followers',
            field=models.ManyToManyField(related_name='Post', through='forums.FollowedPost', to=settings.AUTH_USER_MODEL, verbose_name='Followers'),
        ),
        migrations.AddField(
            model_name='post',
            name='last_comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='last_post_on_topic', to='forums.Comment', verbose_name='Last post on topic'),
        ),
        migrations.AddField(
            model_name='topic',
            name='last_comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='forums.Comment', verbose_name='Last comment in topic'),
        ),
        migrations.AlterUniqueTogether(
            name='followedpost',
            unique_together={('post', 'follower')},
        ),
    ]
