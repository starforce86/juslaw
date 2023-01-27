# Generated by Django 3.0.8 on 2021-05-28 13:26

import apps.users.models.users
from django.conf import settings
import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_fsm
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0023_remove_attorney_is_disciplined'),
    ]

    operations = [
        migrations.CreateModel(
            name='Paralegal',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('verification_status', django_fsm.FSMField(choices=[('not_verified', 'Not verified'), ('approved', 'Approved'), ('denied', 'Denied')], default='not_verified', max_length=20, verbose_name='Verification_status')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, primary_key=True, related_name='paralegal', serialize=False, to=settings.AUTH_USER_MODEL, verbose_name='User')),
                ('phone', models.CharField(help_text="Paralegal's phone number", max_length=128, verbose_name='Phone')),
                ('featured', models.BooleanField(default=False, verbose_name='Is featured')),
                ('biography', models.TextField(blank=True, help_text="Paralegal's legal pratice", null=True, verbose_name='Biography')),
                ('sponsored', models.BooleanField(default=False, help_text='Is paralegal sponsored Jus-Law', verbose_name='Is sponsored')),
                ('sponsor_link', models.URLField(blank=True, help_text='Link to the sponsor of Jus-law', null=True, verbose_name='Sponsor link')),
                ('firm_name', models.CharField(help_text='Firm Name', max_length=100, null=True, verbose_name='Firm name')),
                ('website', models.URLField(blank=True, help_text='Firm website url', null=True, verbose_name='Firm website')),
                ('license_info', models.TextField(help_text="Paralegal's state, agency, date of admission and bar membership number", verbose_name='Licence info')),
                ('is_disciplined', models.BooleanField(default=False, help_text='Have paralegal ever been disciplined (suspended, censured or otherwise disciplined/disqualified as member of legal or any other profession)', verbose_name='Is disciplined')),
                ('practice_description', models.TextField(blank=True, help_text="Description of paralegal's legal practice (1000 characters)", max_length=1000, null=True, verbose_name='Practice description')),
                ('years_of_experience', models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)], verbose_name='How long has paralegal been practicing')),
                ('have_speciality', models.BooleanField(default=True, help_text='Does paralegal have speciality', verbose_name='Have speciality')),
                ('speciality_time', models.PositiveIntegerField(blank=True, help_text='Numbers of years practiced in specialized area', null=True, validators=[django.core.validators.MaxValueValidator(100)], verbose_name='Speciality time')),
                ('speciality_matters_count', models.PositiveIntegerField(blank=True, help_text='Approximate number of matters in last 5 years, handled by paralegal in specialized area', null=True, verbose_name='Speciality matters count')),
                ('fee_rate', models.DecimalField(decimal_places=2, default=0, help_text='How much paralegal take per hour', max_digits=10, verbose_name='Fee rate')),
                ('extra_info', models.TextField(blank=True, help_text='Extra information about paralegal', null=True, verbose_name='Extra information')),
                ('charity_organizations', models.TextField(blank=True, help_text='Name of any volunteer or charitable organizations paralegal workwith or are member of', null=True, verbose_name='Charity organizations')),
                ('keywords', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), default=list, help_text='Based on keywords, opportunities are formed for paralegal', size=None, verbose_name='Keywords')),
                ('appointment_type', models.ManyToManyField(related_name='paralegals', to='users.AppointmentType', verbose_name='AppointmentTypes')),
                ('fee_currency', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paralegals', to='users.Currencies', verbose_name='Fee Currency')),
                ('fee_kinds', models.ManyToManyField(related_name='paralegals', to='users.FeeKind', verbose_name='FeeKinds')),
                ('firm_locations', models.ManyToManyField(help_text="Country, State(s), Address(s), City(s), Zipcode of paralegal's Firm", related_name='paralegals', to='users.FirmLocation', verbose_name='Firm Location')),
                ('followers', models.ManyToManyField(related_name='followed_paralegals', to=settings.AUTH_USER_MODEL, verbose_name='Followers')),
                ('payment_type', models.ManyToManyField(related_name='paralegals', to='users.PaymentType', verbose_name='PaymentType')),
                ('practice_jurisdictions', models.ManyToManyField(help_text='Country, State(s), Agency(s) or federal jurisdiction paralegal are licensed or authorised to practice in', related_name='paralegals', to='users.Jurisdiction', verbose_name='Practice jurisdictions')),
                ('spoken_language', models.ManyToManyField(related_name='paralegals', to='users.Language', verbose_name='SpokenLanguages')),
            ],
            options={
                'verbose_name': 'Paralegal',
                'verbose_name_plural': 'Paralegals',
            },
            bases=(apps.users.models.users.AppUserHelperMixin, models.Model),
        ),
    ]