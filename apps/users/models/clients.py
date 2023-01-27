from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

from ..models import querysets
from .users import AppUserHelperMixin

__all__ = [
    'AbstractClient',
    'Client',
]


class AbstractClient(BaseModel):
    """Model represents common fields between Invite and Client.

    Attributes:
        client_type (str): Type of client(Individual or Firm)
        organization_name (str): Name of client's organization

    """
    INDIVIDUAL_TYPE = 'individual'
    FIRM_TYPE = 'firm'
    TYPES = (
        (INDIVIDUAL_TYPE, _('Individual')),
        (FIRM_TYPE, _('Firm'))
    )

    client_type = models.CharField(
        max_length=50,
        default=INDIVIDUAL_TYPE,
        choices=TYPES,
        verbose_name=_('Type of client'),
        help_text=_('Type of client')
    )

    organization_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Name of organization'),
        help_text=_('Name of organization')
    )

    class Meta:
        abstract = True

    def clean_organization_name(self):
        """Validate `organization_name` field.

        Check two cases:
            That firm client is with name of organization_name.
            That individual client is without name of organization_name.

        """

        if self.client_type == self.FIRM_TYPE and not self.organization_name:
            raise ValidationError(_(
                'Firm clients must have name of organization'
            ))

    @property
    def is_organization(self) -> bool:
        """Return true if client is a `firm`."""
        return self.client_type == self.FIRM_TYPE

    @property
    def display_name(self) -> str:
        """Show client's display name.

        If client is an individual, we show it's full name
        If client is a firm, we show it's organization name

        """
        if self.client_type == self.INDIVIDUAL_TYPE:
            return self.full_name
        return self.organization_name


class Client(AppUserHelperMixin, AbstractClient):
    """Model defines information about client.

    Model describes client's location(US state) and description of help
    it's looking for.

    Attributes:
        user (AppUser): Relation to AppUser
        job(str): Client's job title
        country (cities_light.Country): Location of client
        state (cities_light.Region): Location of client
        city (cities_light.City): Location of client
        address1 (str): Address of client
        address2 (str): Address of client
        zipcode (str): Zipcode of client's address
        help_description (str): Description of help, client is looking for
        client (str): Type of client(Individual or Firm)
        organization_name (str): Name of client's organization

    """

    user = models.OneToOneField(
        'users.AppUser',
        primary_key=True,
        on_delete=models.PROTECT,
        verbose_name=_('User'),
        related_name='client'
    )

    job = models.CharField(
        max_length=128,
        verbose_name=_('Job'),
        help_text=_("Client\'s job title"),
        blank=True,
        null=True
    )

    country = models.ForeignKey(
        'cities_light.Country',
        on_delete=models.SET_NULL,
        related_name='clients',
        verbose_name=_('Client\'s location(country)'),
        null=True,
        blank=True
    )

    state = models.ForeignKey(
        'cities_light.Region',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='clients',
        verbose_name=_('Client\'s location(state)'),
    )

    city = models.ForeignKey(
        'cities_light.City',
        on_delete=models.SET_NULL,
        related_name='clients',
        verbose_name=_('Client\'s location(city)'),
        null=True,
        blank=True
    )

    note = models.TextField(
        verbose_name=_('Note'),
        null=True,
        blank=True
    )

    help_description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Needed help description'),
        help_text=_('What client is looking for help with')
    )

    zip_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_('zip code'),
        help_text=_('Client\'s location(zip code)')
    )

    address1 = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Address1'),
        help_text=_('Client\'s location(address1)')
    )

    address2 = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Address2'),
        help_text=_('Client\'s location(address2)')
    )

    shared_with = models.ManyToManyField(
        'users.AppUser',
        related_name='shared_clients',
        verbose_name=_('Shared with'),
        help_text=_('Users with which client is shared')
    )

    timezone = models.ForeignKey(
        'users.Timezone',
        on_delete=models.SET_NULL,
        related_name='clients',
        null=True,
        blank=True,
        default=587  # Set PST as default
    )

    favorite_attorneys = models.ManyToManyField(
        'Attorney',
        related_name='clients',
        verbose_name='favorite_attorneys',
        help_text=_('Favorite attorney of client')
    )

    objects = querysets.ClientQuerySet.as_manager()

    class Meta:
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')

    @classmethod
    def attorney_clients_and_leads(cls, attorney):
        """Returns leads and clients for the attorney"""
        # only leads
        leads = cls.objects.exclude(
            matters__attorney__in=[attorney.pk],
        ).filter(
            leads__isnull=False,
            leads__attorney=attorney
        ).distinct()
        # actual clients with matters
        clients = cls.objects.filter(
            matters__attorney__in=[attorney.pk],
            matters__attorney=attorney
        ).distinct()

        return leads | clients

    def contacts(self):
        """Return attorneys with whom client is in contact"""
        contacts = set(self.leads.values_list('attorney__user', flat=True))
        contacts |= set(self.leads.values_list('paralegal__user', flat=True))
        contacts |= set(self.leads.values_list('enterprise__user', flat=True))
        contacts |= set(self.matters.values_list('attorney__user', flat=True))
        contacts |= set(self.opportunities.values_list(
            'attorney__user', flat=True
        ))
        return contacts
