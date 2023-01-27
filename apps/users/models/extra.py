from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Speciality(BaseModel):
    """Model defines speciality of attorneys.

    It describes areas of attorneys' speciality

    Examples:
        Personal Injury
        Corporate
        Tax
        Criminal
        Civil Rights

    Attributes:
        title (str): title of speciality
    """

    title = models.CharField(
        max_length=100,
        verbose_name=_('Title'),
        unique=True,
    )
    description = models.TextField(
        verbose_name=_('Description'),
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        'users.AppUser',
        verbose_name=_('Created By'),
        related_name='speciality',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Speciality')
        verbose_name_plural = _('Specialities')

    def __str__(self):
        return self.title


class FeeKind(BaseModel):
    """Model defines fee kind.

    It describes what kinds of fees attorneys will consider

    Examples:
        Flat Fee
        Contingency Fee
        Negotiable Fee
        Alternative Fee

    Attributes:
        title (str): title of fee kind
    """
    title = models.CharField(
        max_length=50,
        verbose_name=_('Title'),
        unique=True,
    )

    class Meta:
        verbose_name = _('Fee Kind')
        verbose_name_plural = _('Fee Kinds')

    def __str__(self):
        return self.title


class Jurisdiction(BaseModel):
    """Model defines jurisdiction.

    Attributes:
        region (cities_light.Region): Region
        country (cities_light.Country): Country
        agency (str): information of jurisdiction
    """
    country = models.ForeignKey(
        'cities_light.Country',
        verbose_name=_('Jurisdiction country'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='jurisdiction'
    )

    state = models.ForeignKey(
        'cities_light.Region',
        verbose_name=_('Jurisdiction state'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='jurisdiction'
    )

    agency = models.CharField(
        max_length=100,
        null=True,
        verbose_name=_('Agency')
    )

    number = models.CharField(
        max_length=20,
        null=True,
        verbose_name=_('Registeration number')
    )

    year = models.CharField(
        max_length=4,
        null=True,
        verbose_name=_('Admitted year')
    )

    class Meta:
        verbose_name = _('Jurisdiction')
        verbose_name_plural = _('Jurisdiction')

    def __str__(self):
        return self.agency or ''


class FirmLocation(BaseModel):
    """Model defines Firm Location.

    Attributes:
        state (cities_light.Region): State
        country (cities_light.Country): Country
        address (str): Address
        city (str): City
        zip_codes (str): ZipCode
    """
    country = models.ForeignKey(
        'cities_light.Country',
        verbose_name=_('Firm country'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='firm_location'
    )

    state = models.ForeignKey(
        'cities_light.Region',
        verbose_name=_('Firm state'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='firm_location'
    )

    city = models.ForeignKey(
        'cities_light.City',
        on_delete=models.SET_NULL,
        verbose_name=_('Firm city'),
        null=True,
        blank=True,
        related_name='firm_location'
    )

    address = models.CharField(
        max_length=100,
        verbose_name=_('Address')
    )

    zip_code = models.CharField(
        max_length=20,
        verbose_name=_('ZipCode')
    )

    class Meta:
        verbose_name = _('FirmLocation')
        verbose_name_plural = _('FirmLocation')

    def __str__(self):
        return self.address


class AppointmentType(BaseModel):
    """Model defines accepted appointment types.

    It describes what types of appointment attorneys will consider

    Examples:
        In-Person Appointments
        Virtual Appointments

    Attributes:
        title (str): type of appointment
    """
    title = models.CharField(
        max_length=50,
        verbose_name=_('Title'),
        unique=True,
    )

    class Meta:
        verbose_name = _('Appointment Type')
        verbose_name_plural = _('Appointment Type')

    def __str__(self):
        return self.title


class PaymentType(BaseModel):
    """Model defines accepted Payment type.

    It describes what types of payment attorneys will consider

    Examples:
        Direct Debit(ACH/eCheck)
        Credit Cards

    Attributes:
        title (str): Payment type
    """
    title = models.CharField(
        max_length=50,
        verbose_name=_('Title'),
        unique=True,
    )

    class Meta:
        verbose_name = _('Payment Type')
        verbose_name_plural = _('Payment Type')

    def __str__(self):
        return self.title


class Language(BaseModel):
    """Model defines spoken language.

    It describes what languages attorneys can speak

    Examples:
        English, Russian

    Attributes:
        title (str): Languages
    """
    title = models.CharField(
        max_length=50,
        verbose_name=_('Title'),
        unique=True,
    )

    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Language')

    def __str__(self):
        return self.title


class Currencies(BaseModel):
    """Model defines currencies

    It describes what currencies attorneys can charge

    Examples:
        USD, GBP, ERU

    Attributes:
        titles (str): Currencies
    """
    title = models.CharField(
        max_length=3,
        verbose_name=_('Currencies'),
        unique=True
    )

    class Meta:
        verbose_name = _('Currencies')
        verbose_name_plural = _('Currencies')

    def __str__(self):
        return self.title


class FirmSize(BaseModel):
    """Model defines firm size

    It describes approximate number of memebers in firm

    Examples:
        2-10, 11-50, 51-100,

    Attributes:
        titles (str): Firm size
    """
    title = models.CharField(
        max_length=10,
        verbose_name=_('Firmsize'),
        unique=True
    )

    class Meta:
        verbose_name = _('Firmsize')
        verbose_name_plural = _('Firmsize')

    def __str__(self):
        return self.title


class TimeZone(BaseModel):
    """Model defines timezone

    It describes all timezone data

    Examples:
        (UTC-08:00) Pacific Time (US & Canada)

    Attribues:
        title(str): Title of timezone
    """

    title = models.TextField(
        verbose_name=_('Timezone'),
    )

    class Meta:
        verbose_name = _('Timezone')
        verbose_name_plural = _('Timezones')

    def __str__(self):
        return self.title
