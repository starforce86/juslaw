# Generated by Django 3.0.9 on 2020-08-21 01:59
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import django_fsm
import model_utils.fields

import apps.users.models.attorney_links
import apps.users.models.users


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial_squashed'),
        ('finance', '0001_initial_squashed'),
    ]

    operations = [
        migrations.AddField(
            model_name='appuser',
            name='active_subscription',
            field=models.ForeignKey(blank=True, help_text='Represents related to user current active stripe subscription', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appuser', to='finance.SubscriptionProxy', verbose_name='Current active subscription'),
        ),
        migrations.CreateModel(
            name='Support',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('verification_status', django_fsm.FSMField(choices=[('not_verified', 'Not verified'), ('approved', 'Approved'), ('denied', 'Denied')], default='not_verified', max_length=20, verbose_name='Verification_status')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, primary_key=True, related_name='support', serialize=False, to=settings.AUTH_USER_MODEL, verbose_name='User')),
                ('description', models.CharField(help_text="User's description (role)", max_length=128, verbose_name='Description')),
                ('payment', models.OneToOneField(blank=True, help_text='Link to payment', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='support', related_query_name='users_support', to='finance.Payment', verbose_name='Payment')),
                ('payment_status', django_fsm.FSMField(choices=[('not_started', 'Not started'), ('payment_in_progress', 'Payment in progress'), ('payment_failed', 'Payment failed'), ('paid', 'Paid')], default='not_started', help_text='Status of payment', max_length=30, verbose_name='Payment Status')),
            ],
            options={
                'verbose_name': 'Paralegal',
                'verbose_name_plural': 'Paralegal users',
            },
            bases=(apps.users.models.users.AppUserHelperMixin, models.Model),
        ),
    ]
