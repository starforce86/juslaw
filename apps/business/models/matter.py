import random
import string
import uuid
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _

from django_fsm import FSMField, transition

from apps.core.models import BaseModel

from .querysets import LeadQuerySet, MatterQuerySet, OpportunityQuerySet

__all__ = (
    'Opportunity',
    'Lead',
    'Matter',
)


def create_matter_code():
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for _ in range(24)
    )


class Opportunity(BaseModel):
    """
    Active chat (contact) between Attorney and Potential Lead

    Attributes:
        client (Client): link to Client participated in a contact
        attorney (Attorney): link to Attorney participated in a contact
        chat_channel (str): Firestore ID of a corresponding chat
        priority (str): priority which Attorney sets to this chat

    TODO: More details to be added later according
        to the requirements/flow for conversion.
    """

    PRIORITY_HIGH = 'high'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_LOW = 'low'

    PRIORITY_CHOICES = (
        (PRIORITY_HIGH, _('High')),
        (PRIORITY_MEDIUM, _('Medium')),
        (PRIORITY_LOW, _('Low'))
    )
    client = models.ForeignKey(
        'users.Client',
        on_delete=models.CASCADE,
        verbose_name=_('Client'),
        related_name='opportunities'
    )
    attorney = models.ForeignKey(
        'users.Attorney',
        on_delete=models.PROTECT,
        verbose_name=_('Attorney'),
        related_name='opportunities'
    )
    chat_channel = models.UUIDField(
        editable=False,
        default=uuid.uuid4,
        verbose_name=_('Chat channel ID'),
        unique=True,
    )

    priority = models.CharField(
        max_length=10,
        verbose_name=_('Opportunity Priority'),
        null=True,
        blank=True,
        choices=PRIORITY_CHOICES,
    )
    objects = OpportunityQuerySet.as_manager()


class Lead(BaseModel):
    """Active chat (contact) between Attorney and Client

    New lead is created from open topics and it means that
    Attorney and Client wants to make some discussions on
    corresponding topic and decide if they want to start
    `matter` (deal) together.

    Attributes:
        post (Post): link to a post in which a contact between Client and
            Attorney was initiated
        client (Client): link to Client participated in a contact
        attorney (Attorney): link to Attorney participated in a contact
        priority (str): priority which Attorney sets to this chat
        chat_channel (str): Firestore ID of a corresponding chat
        status (str):
            Current lead status, it can be: 'active' or 'converted'
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """
    PRIORITY_HIGH = 'high'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_LOW = 'low'

    PRIORITY_CHOICES = (
        (PRIORITY_HIGH, _('High')),
        (PRIORITY_MEDIUM, _('Medium')),
        (PRIORITY_LOW, _('Low'))
    )

    post = models.ForeignKey(
        'forums.Post',
        # attorney able to initiate contact not only through opportunity/topic
        on_delete=models.SET_NULL,
        verbose_name=_('Post'),
        related_name='leads',
        null=True,
        blank=True
    )
    client = models.ForeignKey(
        'users.Client',
        on_delete=models.CASCADE,
        verbose_name=_('Client'),
        related_name='leads'
    )
    attorney = models.ForeignKey(
        'users.Attorney',
        on_delete=models.SET_NULL,
        verbose_name=_('Attorney'),
        related_name='leads',
        null=True
    )
    paralegal = models.ForeignKey(
        'users.Paralegal',
        on_delete=models.SET_NULL,
        verbose_name=_('Paralegal'),
        related_name='leads',
        null=True
    )
    enterprise = models.ForeignKey(
        'users.Enterprise',
        on_delete=models.SET_NULL,
        verbose_name=_('Enterprises'),
        related_name='leads',
        null=True
    )
    priority = models.CharField(
        max_length=10,
        verbose_name=_('Lead Priority'),
        null=True,
        blank=True,
        choices=PRIORITY_CHOICES,
    )
    chat_channel = models.UUIDField(
        editable=False,
        default=uuid.uuid4,
        verbose_name=_('Chat channel ID'),
        unique=True,
    )

    STATUS_ACTIVE = 'active'
    STATUS_CONVERTED = 'converted'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _('Active')),
        (STATUS_CONVERTED, _('Converted')),
    )

    status = FSMField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name=_('Status')
    )

    objects = LeadQuerySet.as_manager()

    class Meta:
        verbose_name = _('Lead')
        verbose_name_plural = _('Leads')
        unique_together = ('client', 'attorney')

    def __str__(self):
        return f'Chat between {self.client} and {self.attorney}'

    @property
    def is_converted(self):
        """Check if lead is converted."""
        return self.status == self.STATUS_CONVERTED


class Matter(BaseModel):
    """Matter model

    Represents a work relationships between Attorney and Client, a kind of
    agreement with predefined rate, type of work and etc.

    Attributes:
        lead (Lead): link to contact (chat) from which matter was created
        client (Client): link to a client - customer of matter
        attorney (Attorney): link to attorney which work on the matter
        code (str): special alphabetic code (identifier)
        title (str): matter title
        description (text): simple matter description in simple words
        rate (decimal): amount of money taken by rate type in $
        country (Country): country of the matter's jurisdiction
        state (Region): state of the matter's jurisdiction
        city (City): city of the matter's jurisdiction
        status (str): current matter status, is it opened or closed
        stage (Stage): custom matter's stage created by Attorney
        completed (datetime): timestamp when the matter was closed
        shared_with (AppUser): list of users with which matter is shared
        referral (Referral): Referral request from other attorney
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    There are following possible billing systems:

        1. Hourly Rate = `rate` * amount of billed hours -> system creates
        invoice

        2. Fixed Set Amount =  `rate` for record -> no invoice generated
        (attorney still bills time to track conflicts)

        3. Contingency Fee =  `rate` for record -> no invoice generated
        (attorney still bills time to track conflicts)

        4. Alternative Agreement =  `rate` for record -> no invoice generated
        (attorney still bills time to track conflicts)

    """

    # TODO: clarify restrictions on statuses updates
    #  statuses are transitioned by simple buttons on frontend side
    STATUS_OPEN = 'open'
    STATUS_REFERRAL = 'referral'
    STATUS_CLOSE = 'close'

    STATUS_CHOICES = (
        (STATUS_OPEN, _('Open')),
        (STATUS_REFERRAL, ('Referral')),
        (STATUS_CLOSE, _('Close')),
    )

    STATUS_TRANSITION_MAP = {
        STATUS_OPEN: 'open',
        STATUS_REFERRAL: 'referral',
        STATUS_CLOSE: 'close',
    }

    lead = models.ForeignKey(
        'business.Lead',
        # matter can exist without a lead, so it can be easily deleted
        on_delete=models.SET_NULL,
        verbose_name=_('Lead'),
        related_name='matters',
        null=True,
        blank=True
    )
    invite = models.ForeignKey(
        'users.Invite',
        verbose_name=_('Invite'),
        related_name='matters',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING
    )
    client = models.ForeignKey(
        'users.Client',
        on_delete=models.CASCADE,
        verbose_name=_('Client'),
        related_name='matters',
        null=True,
        blank=True,
    )
    attorney = models.ForeignKey(
        'users.Attorney',
        on_delete=models.SET_NULL,
        verbose_name=_('Attorney'),
        related_name='matters',
        null=True
    )
    code = models.CharField(
        max_length=25,
        verbose_name=_('Code'),
        help_text=_('Simple alphabetical code (identifier) of a matter'),
        default=create_matter_code
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title')
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Start date")
    )
    close_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Close date")
    )
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Extra matter description')
    )
    speciality = models.ForeignKey('users.Speciality',
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True,
                                   verbose_name=_("Speciality"))
    currency = models.ForeignKey(
        'users.Currencies',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Currency")
    )

    rate = models.DecimalField(
        max_digits=30,
        decimal_places=2,
        verbose_name=_('Rate'),
        help_text=_('Amount of money taken for a rate type in $'),
        default=0
    )
    rate = models.CharField(
        max_length=50,
        verbose_name=_('Rate'),
        help_text=_('Amount of money taken for a rate type in $'),
    )
    country = models.ForeignKey(
        'cities_light.Country',
        on_delete=models.SET_NULL,
        related_name='matters',
        verbose_name=_('Country'),
        null=True,
        blank=True
    )
    state = models.ForeignKey(
        'cities_light.Region',
        on_delete=models.SET_NULL,
        related_name='matters',
        verbose_name=_('State'),
        null=True,
        blank=True
    )
    city = models.ForeignKey(
        'cities_light.City',
        on_delete=models.SET_NULL,
        related_name='matters',
        verbose_name=_('City'),
        null=True,
        blank=True
    )
    is_billable = models.BooleanField(
        default=False,
        verbose_name=_("Is billable")
    )
    fee_type = models.ForeignKey(
        'users.FeeKind',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Fee type")
    )
    fee_note = models.TextField(
        default='',
        max_length=255,
        verbose_name='Fee note'
    )

    status = FSMField(
        max_length=15,
        choices=STATUS_CHOICES,
        # default=STATUS_DRAFT,
        default=STATUS_OPEN,
        verbose_name=_('Status')
    )
    stage = models.ForeignKey(
        'Stage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Stage'),
        related_name='matters',
    )
    completed = models.DateTimeField(
        verbose_name=_('Completed datetime'),
        help_text=_('Datetime when the matter was completed(closed)'),
        null=True,
        blank=True
    )
    shared_with = models.ManyToManyField(
        to='users.AppUser',
        related_name='shared_matters',
        through='MatterSharedWith',
        verbose_name=_('Shared with'),
        help_text=_('Users with which matter is shared')
    )
    referral = models.ForeignKey(
        'Referral',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Referral'),
        related_name='matters',
    )

    objects = MatterQuerySet.as_manager()

    class Meta:
        verbose_name = _('Matter')
        verbose_name_plural = _('Matters')
        unique_together = ['attorney', 'code']
        constraints = [
            models.CheckConstraint(
                check=Q(client__isnull=False) | Q(invite__isnull=False),
                name='One of the client or invite should not be null'
            )
        ]

    def __str__(self):
        return f'{self.title}'

    def clean_code(self):
        """Check that code is unique for attorney."""
        self.code = self.code.upper()
        duplicate = self.__class__.objects.filter(
            code=self.code, attorney_id=self.attorney_id,
        ).exclude(pk=self.pk)
        if duplicate.exists():
            raise ValidationError(
                f'Matter with code:`{self.code}` is already exist'
            )

    def clean_lead(self):
        """Validate lead data.

        Check that Matter `attorney` is the same as related Lead one.

        """
        if not self.lead_id:
            return

        if self.attorney_id != self.lead.attorney_id:
            raise ValidationError(_(
                "Matter's `attorney` doesn't match from matter's lead"
            ))

    def clean_stage(self):
        """Check that stage belong to matter's attorney."""
        if not self.stage_id:
            return

        if self.stage.attorney_id != self.attorney_id:
            raise ValidationError(_(
                "Stage doesn't belong to this attorney"
            ))

    def can_change_status(self, user):
        """Return ``True`` if ``user`` can change matter's `status`.

        Matter's status can be changed only by matter's original `attorney` or
        users with which the matter was shared.

        """
        return user.pk == self.attorney_id or self.is_shared_for_user(user)

    def is_shared_for_user(self, user):
        """Return `True` if matter is shared for user."""
        if hasattr(self, '_is_shared'):
            return self._is_shared
        return bool(self.shared_with.filter(id=user.id).exists())

    def delete_referral(self):
        """
        Delete the referral object belong to matter once attorney approved
        """
        if self.status == Matter.STATUS_REFERRAL:
            self.attorney = self.referral.attorney
            self.referral.delete()
            self.referral = None

    @property
    def referral_pending(self):
        """Return ``True`` if user sends referral"""
        # return self.referral.attorney.user
        return True

    @property
    def referral_request(self):
        """Return ``True`` if user receives referral"""
        # return self.attorney.user
        return True

    @property
    def is_open(self):
        """Designate whether matter has a `open` status."""
        return self.status == Matter.STATUS_OPEN

    @transition(field=status,
                target=STATUS_OPEN,
                permission=can_change_status)
    def open(self, user=None):
        """Update matter status to `open`."""
        # Escape import error
        from ...users.models import UserStatistic
        from ...users.services import create_stat
        if self.referral is not None:
            self.referral.delete()
            self.referral = None
        create_stat(
            user=self.attorney.user, tag=UserStatistic.TAG_OPEN_MATTER
        )

    @transition(field=status,
                source=STATUS_OPEN,
                target=STATUS_REFERRAL,
                permission=can_change_status)
    def send_referral(self, user=None):
        """Update matter status to `open`."""
        # Escape import error
        from ...users.models import UserStatistic
        from ...users.services import create_stat
        create_stat(
            user=self.attorney.user, tag=UserStatistic.TAG_REFERRED_MATTER
        )

    @transition(field=status,
                source=STATUS_REFERRAL,
                target=STATUS_OPEN,
                permission=can_change_status)
    def accept_referral(self, user=None):
        """Update matter status to `open`."""
        # Escape import error
        from ...users.models import UserStatistic
        from ...users.services import create_stat
        create_stat(
            user=self.attorney.user, tag=UserStatistic.TAG_OPEN_MATTER
        )

    @transition(field=status,
                source=STATUS_REFERRAL,
                target=STATUS_OPEN,
                permission=can_change_status)
    def ignore_referral(self, user=None):
        """Update matter status to `open`."""
        # Escape import error
        from ...users.models import UserStatistic
        from ...users.services import create_stat
        if self.referral is not None:
            self.referral.delete()
            self.referral = None
        create_stat(
            user=self.attorney.user, tag=UserStatistic.TAG_OPEN_MATTER
        )

    @transition(field=status,
                source=STATUS_OPEN,
                target=STATUS_CLOSE,
                permission=can_change_status)
    def close(self, user=None):
        """Update matter status to `close`.

        Also add close matter statistic to attorney.

        """
        # Escape import error
        from ...users.models import UserStatistic
        from ...users.services import create_stat
        if self.referral is not None:
            self.referral.delete()
            self.referral = None
        create_stat(
            user=self.attorney.user, tag=UserStatistic.TAG_CLOSE_MATTER
        )
        self.close_date = date.today()

    @property
    def time_billed(self) -> timedelta:
        """Returns sum of matter `spent time` in jobs logs."""
        # try to get already calculated from `with_totals` qs values
        if hasattr(self, '_time_billed'):
            return self._time_billed

        time_billed = self.billing_item.aggregate(Sum('time_spent'))
        return time_billed['time_spent__sum']

    @property
    def fees_earned(self) -> timedelta or None:
        """Returns sum of matter `fees` in jobs logs."""
        # if matter is not `hourly` rated return None
        if not self.is_hourly_rated:
            return

        # try to get already calculated from `with_totals` qs values
        if hasattr(self, '_fees_earned'):
            return self._fees_earned

        fees_earned = sum([obj.fee for obj in self.billing_item.all()])
        return fees_earned

    @property
    def is_hourly_rated(self) -> bool:
        """Returns flag if matter has `hourly` `rate_type`."""
        return self.fee_type is not None and self.fee_type.id == 3

    def save(self, **kwargs):
        """Save code as upper case."""
        self.code = self.code.upper()
        super().save(**kwargs)

    @classmethod
    def get_by_invite(cls, invite):
        return cls.objects.filter(
            invite=invite
        )
