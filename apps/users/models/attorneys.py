import uuid

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


class Attorney(AppUserHelperMixin, VerifiedRegistration):
    """Model defines information about attorneys.

    Model describes attorney's education, experience, speciality, fees
    and extra information about attorney.

    Notes:
        User can only have one attorney profile.
        Attorney must have either bar_number or registration_number.
        We target fields' help_text to frontend team not app users. Reason is
        drf_yasg uses it to describe fields in serializers.
        After user submitted it's Attorney profile, it's account becomes
        inactive until it's Attorney profile is approved by admins.
        We don't use any google map api integrations, all location data comes
        from front-end

    Attributes:
        user (AppUser): Relation to AppUser
        verification_status (str):
            Verification_status of attorney, there three statuses:
                not_verified - Default on submission
                approved - Approved by admins
                denied - Denied by admins
        featured(bool):
            If attorney has Premium subscription it becomes featured attorney
            on clients search
        sponsored(bool):
            If attorney is somehow sponsored Jus-Law, then admin set this field
            to true and this attorney will show up on special place on main
            page of site. (It's alternative to featured)
        sponsor_link(str):
            Link to Jus-law's sponsor. Will be used on front-end part.
        followers(AppUser):
            Users that follow attorney. They will get notifications about
            attorney activity
        firm_name(str): Name of firm where attorny is located
        website(url): URL of firm
        firm_locations (dict):
            Name of country, state, city, address, zip code where attorney is
            located
        practice_jurisdictions (dict):
            Name of country, region, agency where attorney is located
        license_info (str):
            Attorney's state, agency, date of admission and bar membership
            number
        practice_description (str): Description of attorney's legal practice
        years_of_experience (int): Years of attorney experience
        have_speciality (bool): Does attorney have speciality
        speciality_time (int): Numbers of years practiced in specialized area
        speciality_matters_count (int):
            Approximate number of matters in last 5 years, handled by attorney
            in specialized area
        fee_rate (decimal): How much attorney take per hour
        fee_types (FeeKind): Kinds of fees accepted by attorney
        extra_info (str): Extra information about attorney
        charity_organizations (str):
            Name of any volunteer or charitable organizations attorney work
            with or are member of
        keywords (List[str]): Use in search of attorney's opportunities
        is_submittable_potential(boolean): Is submittable proposal
            for potential client
    """
    user = models.OneToOneField(
        'users.AppUser',
        primary_key=True,
        on_delete=models.PROTECT,
        verbose_name=_('User'),
        related_name='attorney'
    )

    followers = models.ManyToManyField(
        'users.AppUser',
        verbose_name=_('Followers'),
        related_name='followed_attorneys'
    )

    featured = models.BooleanField(
        default=False,
        verbose_name=_('Is featured')
    )

    biography = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Biography'),
        help_text=_('Attorney\'s legal pratice')
    )

    # Sponsor information

    sponsored = models.BooleanField(
        default=False,
        verbose_name=_('Is sponsored'),
        help_text=_('Is attorney sponsored Jus-Law')
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
        related_name='attorneys',
        verbose_name=_('Firm Location'),
        help_text=_(
            'Country, State(s), Address(s), City(s), Zipcode '
            'of attorney\'s Firm'
        )
    )

    # Practice

    practice_jurisdictions = models.ManyToManyField(
        'Jurisdiction',
        related_name='attorneys',
        verbose_name=_('Practice jurisdictions'),
        help_text=_(
            'Country, State(s), Agency(s) or federal jurisdiction attorney'
            ' are licensed or authorised to practice in'
        )
    )

    license_info = models.TextField(
        verbose_name=_('Licence info'),
        help_text=_(
            "Attorney's state, agency, date of admission "
            "and bar membership number"
        ),
    )

    practice_description = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name=_('Practice description'),
        help_text=_(
            'Description of attorney\'s legal practice (1000 characters)'
        )
    )

    years_of_experience = models.PositiveIntegerField(
        validators=(
            MaxValueValidator(100),
        ),
        verbose_name=_('How long has attorney been practicing'),
        default=0
    )

    # Speciality

    have_speciality = models.BooleanField(
        default=True,
        verbose_name=_('Have speciality'),
        help_text=_(
            'Does attorney have speciality'
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
            'attorney in specialized area'
        )
    )

    # Service Fees

    fee_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Fee rate'),
        help_text=_('How much attorney take per hour'),
        null=True,
        default=None
    )

    fee_types = models.ManyToManyField(
        'FeeKind',
        verbose_name=_('FeeKinds'),
        related_name='attorneys'
    )

    appointment_type = models.ManyToManyField(
        'AppointmentType',
        verbose_name=_('AppointmentTypes'),
        related_name='attorneys'
    )

    payment_type = models.ManyToManyField(
        'PaymentType',
        verbose_name=_('PaymentType'),
        related_name='attorneys'
    )

    spoken_language = models.ManyToManyField(
        'Language',
        blank=True,
        verbose_name=_('SpokenLanguages'),
        related_name='attorneys'
    )

    fee_currency = models.ForeignKey(
        'Currencies',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Fee Currency'),
        related_name='attorneys'
    )

    # Additional information

    extra_info = models.TextField(
        verbose_name=_('Extra information'),
        null=True,
        blank=True,
        help_text=_('Extra information about attorney')
    )

    charity_organizations = models.TextField(
        verbose_name=_('Charity organizations'),
        null=True,
        blank=True,
        help_text=_(
            'Name of any volunteer or charitable organizations attorney work'
            'with or are member of'
        )
    )

    keywords = ArrayField(
        models.CharField(max_length=255),
        default=list,
        verbose_name=_('Keywords'),
        help_text=_(
            'Based on keywords, opportunities are formed for attorney'
        ),
    )

    is_submittable_potential = models.BooleanField(
        default=False,
        verbose_name=_('Is Submittable Potential'),
        help_text=_(
            'Sumbit proposals for potential client engagments'
        )
    )

    industry_contacts = models.ManyToManyField(
        'users.AppUser',
        related_name='contacted_attorney',
        verbose_name=_('Industry Contacts'),
        through='AttorneyIndustryContacts'
    )

    # tax
    tax_rate = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        verbose_name=_('Tax rate'),
        help_text=_('Tax rate'),
        null=True,
        default=None
    )

    objects = querysets.AttorneyQuerySet.as_manager()

    class Meta:
        verbose_name = _('Attorney')
        verbose_name_plural = _('Attorneys')

    def clean_sponsor_link(self):
        """Check that only sponsored attorney has a link."""
        if self.sponsor_link and not self.sponsored:
            raise ValidationError(_(
                'Only sponsored attorneys can have sponsored links'
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

        After successful user verification by admin send `attorney_verified`
        signal.

        """
        from ..signals import attorney_verified
        attorney_verified.send(
            sender=self.user._meta.model,
            instance=self.user
        )


class AttorneyIndustryContacts(models.Model):
    attorney = models.ForeignKey(
        'Attorney',
        on_delete=models.CASCADE,
        verbose_name=_('Attorney')
    )
    industry_contact = models.ForeignKey(
        'users.AppUser',
        on_delete=models.CASCADE,
        verbose_name=_('Industry Contact')
    )
    chat_channel = models.UUIDField(
        editable=False,
        default=uuid.uuid4,
        verbose_name=_('Chat channel ID'),
        unique=True,
    )
