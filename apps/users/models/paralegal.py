from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.models.utils.verification import VerifiedRegistration

from ...finance.services import stripe_subscriptions_service
from . import querysets
from .users import AppUserHelperMixin


class Paralegal(AppUserHelperMixin, VerifiedRegistration):
    """Model defines information about paralegals.

    Model describes  paralegal's education, experience, speciality, fees
    and extra information about  paralegal.

    Notes:
        User can only have one paralegal profile.
        Paralegal must have either bar_number or registration_number.
        We target fields' help_text to frontend team not app users. Reason is
        drf_yasg uses it to describe fields in serializers.
        After user submitted it's Paralegal profile, it's account becomes
        inactive until it's Paralegal profile is approved by admins.
        We don't use any google map api integrations, all location data comes
        from front-end

    Attributes:
        user (AppUser): Relation to AppUser
        role(str): Specify Your Role
        verification_status (str):
            Verification_status of paralegal, there three statuses:
                not_verified - Default on submission
                approved - Approved by admins
                denied - Denied by admins
        featured(bool):
            If paralegal has Premium subscription it becomes featured paralegal
            on clients search
        sponsored(bool):
            If paralegal is somehow sponsored Jus-Law, then admin set this
            field to true and this paralegal will show up on special place on
            main page of site. (It's alternative to featured)
        sponsor_link(str):
            Link to Jus-law's sponsor. Will be used on front-end part.
        followers(AppUser):
            Users that follow paralegal. They will get notifications about
            paralegal activity
        firm_locations (dict):
            Name of country, state, city, address, zip code where attorney is
            located
        practice_jurisdictions (dict):
            Name of country, region, agency where attorney is located
        license_info (str):
            Paralegal's state, agency, date of admission and bar membership
            number
        practice_description (str): Description of paralegal's legal practice
        years_of_experience (int): Years of paralegal experience
        have_speciality (bool): Does paralegal have speciality
        speciality_time (int): Numbers of years practiced in specialized area
        speciality_matters_count (int):
            Approximate number of matters in last 5 years, handled by paralegal
            in specialized area
        fee_rate (decimal): How much paralegal take per hour
        fee_types (FeeKind): Kinds of fees accepted by paralegal
        extra_info (str): Extra information about paralegal
        charity_organizations (str):
            Name of any volunteer or charitable organizations paralegal work
            with or are member of
        keywords (List[str]): Use in search of paralegal's opportunities

    """
    user = models.OneToOneField(
        'users.AppUser',
        primary_key=True,
        on_delete=models.PROTECT,
        verbose_name=_('User'),
        related_name='paralegal'
    )

    role = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name=_('Role'),
        help_text=_("Other's special role"),
    )

    followers = models.ManyToManyField(
        'users.AppUser',
        verbose_name=_('Followers'),
        related_name='followed_paralegals'
    )

    featured = models.BooleanField(
        default=False,
        verbose_name=_('Is featured')
    )

    biography = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Biography'),
        help_text=_('Paralegal\'s legal pratice')
    )

    # Sponsor information

    sponsored = models.BooleanField(
        default=False,
        verbose_name=_('Is sponsored'),
        help_text=_('Is paralegal sponsored Jus-Law')
    )

    sponsor_link = models.URLField(
        null=True,
        blank=True,
        verbose_name=_('Sponsor link'),
        help_text=_('Link to the sponsor of Jus-law')
    )

    # Location

    firm_name = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name=_('Firm name'),
        help_text=_('Firm Name')
    )

    website = models.URLField(
        null=True,
        blank=True,
        verbose_name=_('Firm website'),
        help_text=_('Firm website url')
    )

    firm_locations = models.ManyToManyField(
        'FirmLocation',
        related_name='paralegals',
        verbose_name=_('Firm Location'),
        help_text=_(
            'Country, State(s), Address(s), City(s), Zipcode '
            'of paralegal\'s Firm'
        )
    )

    # Practice

    practice_jurisdictions = models.ManyToManyField(
        'Jurisdiction',
        related_name='paralegals',
        verbose_name=_('Practice jurisdictions'),
        help_text=_(
            'Country, State(s), Agency(s) or federal jurisdiction paralegal'
            ' are licensed or authorised to practice in'
        )
    )

    license_info = models.TextField(
        verbose_name=_('Licence info'),
        help_text=_(
            "Paralegal's state, agency, date of admission "
            "and bar membership number"
        ),
    )

    practice_description = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name=_('Practice description'),
        help_text=_(
            'Description of paralegal\'s legal practice (1000 characters)'
        )
    )

    years_of_experience = models.PositiveIntegerField(
        validators=(
            MaxValueValidator(100),
        ),
        verbose_name=_('How long has paralegal been practicing'),
        default=0
    )

    # Speciality

    have_speciality = models.BooleanField(
        default=True,
        verbose_name=_('Have speciality'),
        help_text=_(
            'Does paralegal have speciality'
        )
    )

    speciality_time = models.PositiveIntegerField(
        validators=(
            MaxValueValidator(100),
        ),
        null=True,
        blank=True,
        verbose_name=_('Speciality time'),
        help_text=_('Numbers of years practiced in specialized area')
    )

    speciality_matters_count = models.PositiveIntegerField(
        verbose_name=_('Speciality matters count'),
        null=True,
        blank=True,
        help_text=_(
            'Approximate number of matters in last 5 years, handled by '
            'paralegal in specialized area'
        )
    )

    # Service Fees

    fee_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Fee rate'),
        help_text=_('How much paralegal take per hour'),
        default=0
    )

    fee_types = models.ManyToManyField(
        'FeeKind',
        verbose_name=_('FeeKinds'),
        related_name='paralegals'
    )

    payment_type = models.ManyToManyField(
        'PaymentType',
        verbose_name=_('PaymentType'),
        related_name='paralegals'
    )

    spoken_language = models.ManyToManyField(
        'Language',
        blank=True,
        verbose_name=_('SpokenLanguages'),
        related_name='paralegals'
    )

    fee_currency = models.ForeignKey(
        'Currencies',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Fee Currency'),
        related_name='paralegals'
    )

    # Additional information

    extra_info = models.TextField(
        verbose_name=_('Extra information'),
        null=True,
        blank=True,
        help_text=_('Extra information about paralegal')
    )

    charity_organizations = models.TextField(
        verbose_name=_('Charity organizations'),
        null=True,
        blank=True,
        help_text=_(
            'Name of any volunteer or charitable organizations paralegal work'
            'with or are member of'
        )
    )

    keywords = ArrayField(
        models.CharField(max_length=255),
        default=list,
        verbose_name=_('Keywords'),
        help_text=_(
            'Based on keywords, opportunities are formed for paralegal'
        ),
    )

    objects = querysets.ParalegalQuerySet.as_manager()

    class Meta:
        verbose_name = _('Paralegal')
        verbose_name_plural = _('Paralegals')

    def clean_sponsor_link(self):
        """Check that only sponsored paralegal has a link."""
        if self.sponsor_link and not self.sponsored:
            raise ValidationError(_(
                'Only sponsored paralegal can have sponsored links'
            ))

    def post_verify_hook(self, **kwargs):
        """Separate hook to add custom `verification` business logic.

        Add `paid` subscription creation if stripe is enabled.

        """
        # For example, local development does not require creation
        # a stripe subscription
        if settings.STRIPE_ENABLED:
            stripe_subscriptions_service.create_initial_subscription(
                user=self.user,
                trial_end=kwargs['trial_end']
            )

    def post_verify_by_admin_hook(self, **kwargs):
        """Separate hook to add custom `verification` business logic.

        After successful user verification by admin send `paralegal_verified`
        signal.

        """
        from ..signals import paralegal_verified
        paralegal_verified.send(
            sender=self.user._meta.model,
            instance=self.user
        )
