import uuid as uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

from ..models import querysets
# from .clients import AbstractClient
from .users import AppUser

__all__ = [
    'Invite',
]


class Invite(BaseModel):
    """Model defines different users invitations from the app.

    It used in cases when attorney and other user (client or attorney) meet
    outside site, and attorney wants to work with him through the app.

    There are following possible invitation types:

        - attorney invites client, there should be filled `first_name`,
        `last_name`, `email`, `message`, `inviter` fields (`invited_by_user`
        type).

        - attorney invites another attorney from `share matter`, there should
        be filled `email`, `title`, `message`, `matter`, `inviter` fields. So
        when attorney is registered and verified - he would get an email that
        some matter was shared with him (`invited_by_user` type).

        - imported from another sources users (WordPress website), there should
        be filled `email`, `first_name`, `last_name`, `specialties`, `phone`,
        `help_description` (`imported` type).

    Attributes:
        uuid (str):
            Primary key of invitation, used to make unique invitation link
            in email message.
        inviter (AppUser): The Attorney, who created invitation.
        user (AppUser):
            If invited person accept this invitation, we will store new
            registered user.
        user_type(str): Type of invited user can be
                            client
                            attorney
                            paralegal
                            lead
        type(str):
            Type on invitation
            invited_by_user - created through api
            imported - created through django import export
        first_name (str): First name of invited user.
        middle_name (str): Middle name of invited contact - optional
        last_name (str): Last name of invited user.
        email (str): Email of invited user.
        message (str): Message of invitation - optional
        sent (datetime): Time when invitation was sent.
        note (str): Any client related note attorney can add. - optional
        zip_code (str): Zip code of the invited contact - optional
        address (str): Address of the invited contact - optional
        country (str): Country of the invited contact - optional
        state (str): State of the invited contact - optional
        city (str): City of the invited contact - optional
        role (str): Role of the invited contact - optional

        client_type (str): Type of client(Client or Lead)
        organization_name (str): Name of invintee's organization

        Extra information from sharing matters UI:
        title (str): Title of invitation
        matter (Matter): matter that will be shared after user registration

        Extra information from WordPress:
        specialities(Speciality): List specialities picked in WordPress
        help_description(str): Help description stated WordPress
        phone(str): Phone stated WordPress

    """
    CLIENT_TYPE_CLIENT = 'client'
    CLIENT_TYPE_LEAD = 'lead'
    TYPES = (
        (CLIENT_TYPE_CLIENT, _('client')),
        (CLIENT_TYPE_LEAD, _('lead'))
    )
    client_type = models.CharField(
        max_length=50,
        choices=TYPES,
        null=True,
        blank=True,
        verbose_name=_('Type of invitee'),
        help_text=_('Type of invitee')
    )
    uuid = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        verbose_name=_('UUID'),
        help_text=_(
            'Primary key of invitation, used to make unique invitation link'
        )
    )

    inviter = models.ForeignKey(
        'users.AppUser',
        on_delete=models.PROTECT,
        verbose_name=_('Inviter'),
        related_name='sent_invitations',
        null=True
    )

    user = models.ForeignKey(
        'users.AppUser',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('User'),
        related_name='invitations'
    )

    USER_TYPE_CLIENT = 'client'
    USER_TYPE_ATTORNEY = 'attorney'
    USER_TYPE_PARALEGAL = 'paralegal'
    USER_TYPE_LEAD = 'lead'
    USER_TYPES = (
        (USER_TYPE_CLIENT, _('Client')),
        (USER_TYPE_ATTORNEY, _('Attorney')),
        (USER_TYPE_PARALEGAL, _('Paralegal')),
        (USER_TYPE_LEAD, _('Lead')),
    )

    user_type = models.CharField(
        max_length=10,
        default=USER_TYPE_CLIENT,
        choices=USER_TYPES,
        verbose_name=_('Type of invited user')
    )
    note = models.TextField(
        verbose_name=_('Note'),
        null=True,
        blank=True
    )
    TYPE_IMPORTED = 'imported'
    TYPE_INVITED = 'invited_by_user'
    TYPES = (
        (TYPE_IMPORTED, _('Imported')),
        (TYPE_INVITED, _('Invited by user')),
    )

    type = models.CharField(
        max_length=20,
        default=TYPE_INVITED,
        choices=TYPES,
        verbose_name=_('Type of invitation')
    )

    first_name = models.CharField(
        verbose_name=_('First name'),
        max_length=30,
    )

    last_name = models.CharField(
        verbose_name=_('Last name'),
        max_length=150,
    )

    middle_name = models.CharField(
        verbose_name=_('Middle name'),
        max_length=150,
        null=True,
        blank=True
    )

    email = models.EmailField(
        verbose_name=_('E-mail address'),
    )

    message = models.TextField(
        verbose_name=_('Message'),
        help_text=_('Message of invitation'),
        null=True,
        blank=True
    )

    sent = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Sent at'),
        help_text=_('Time when invitation was sent')
    )

    # Extra information from sharing matters UI

    title = models.CharField(
        max_length=256,
        verbose_name=_('Title'),
        help_text=_('Title'),
        blank=True,
        null=True
    )

    matter = models.ForeignKey(
        'business.Matter',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Matter'),
        related_name='invitations'
    )
    zip_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_('zip code'),
        help_text=_('Invited contact\'s location(zip code)')
    )

    address = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Address1'),
        help_text=_('Invited contact\'s location(address1)')
    )
    state = models.ForeignKey(
        'cities_light.Region',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='contacts_state',
        verbose_name=_('State'),
        help_text=_('Invited contact\'s state')
    )
    country = models.ForeignKey(
        'cities_light.Country',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='contacts_country',
        verbose_name=_('Country'),
        help_text=_('Invited contact\'s country')
    )
    city = models.ForeignKey(
        'cities_light.City',
        on_delete=models.SET_NULL,
        verbose_name=_('City'),
        null=True,
        blank=True,
        related_name='contacts_city'
    )
    role = models.CharField(
        max_length=128,
        verbose_name=_('role'),
        help_text=_("Invited contact\'s job title"),
        blank=True,
        null=True
    )

    # Extra information from WordPress for imported users

    specialities = models.ManyToManyField(
        'Speciality',
        verbose_name=_('Specialities'),
        related_name='invites'
    )

    help_description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Needed help description'),
        help_text=_('What client is looking for help with')
    )

    phone = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name=_('Phone'),
        help_text=_("Attorney's phone number"),
    )

    shared_with = models.ManyToManyField(
        'users.AppUser',
        related_name='shared_invitees',
        verbose_name=_('Shared with'),
        help_text=_('Users with which invitee is shared')
    )

    organization_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Name of organization'),
        help_text=_('Name of organization')
    )

    objects = querysets.InviteQuerySet.as_manager()

    class Meta:
        verbose_name = _('Invitation')
        verbose_name_plural = _('Invitations')

    def __str__(self):
        return (
            f'{self.inviter}\'s invitation '
            f'for {self.first_name} {self.last_name}'
        )

    @property
    def full_name(self):
        """Get invited user's full_name."""
        if self.user:
            return self.user.full_name
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return None

    def clean_email(self):
        """Check that user with email stated in invitation doesn't exists."""
        user_in_db = AppUser.objects.filter(email__iexact=self.email).first()
        if not self.user and user_in_db:
            raise ValidationError(
                'User with such email is already registered',
                params={
                    'user_pk': user_in_db.pk,
                    'user_type': user_in_db.user_type
                }
            )

    @classmethod
    def get_pending_attorney_invites(cls, attorney):
        """Returns pending invites for a given attorney."""
        return cls.objects.filter(
            inviter=attorney.user,
            user__isnull=True,
            user_type__in=[cls.USER_TYPE_CLIENT, cls.USER_TYPE_LEAD]
        )

    @classmethod
    def get_pending_paralegal_invites(cls, paralegal):
        """Returns pending invites for a given paralegal."""
        return cls.objects.filter(
            inviter=paralegal.user,
            user__isnull=True,
            user_type__in=[cls.USER_TYPE_CLIENT, cls.USER_TYPE_LEAD]
        )

    @classmethod
    def get_pending_attorney_invites_for_industry_contacts(cls, attorney):
        return cls.objects.filter(
            inviter=attorney.user,
            user__isnull=True,
            user_type__in=[cls.USER_TYPE_PARALEGAL, cls.USER_TYPE_ATTORNEY]
        )
