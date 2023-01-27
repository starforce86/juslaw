from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_fsm import FSMField, transition

from apps.core.models import BaseModel
from apps.forums.models import ForumPracticeAreas
from apps.users.models.extra import Currencies


class PostedMatter(BaseModel):
    """
    Attributes:
        client (CLient): Client who created the matter post
        title (str): matter title
        description (text): simple matter description in simple words
        budget (float): the amount of client budget
        budget type(str): can be
            hourly
            flat_fee
            contingency_fee
            other_fee
        currency (str): client currency
    """
    client = models.ForeignKey(
        'users.Client',
        on_delete=models.CASCADE,
        verbose_name=_('Client'),
        related_name='posted_matters'
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title')
    )
    practice_area = models.ForeignKey(
        ForumPracticeAreas,
        verbose_name=_('Related practice area'),
        on_delete=models.PROTECT,
        related_name='posted_matter',
        null=True,
        blank=True,
    )
    BUDGET_TYPE_HOURLY = 'hourly'
    BUDGET_TYPE_FLAT = 'flat_fee'
    BUDGET_TYPE_CONTINGENCY_FEE = 'contingency_fee'
    BUDGET_TYPE_OTHER = 'other'

    BUDGET_TYPE_CHOICES = (
        (BUDGET_TYPE_HOURLY, _('Hourly')),
        (BUDGET_TYPE_FLAT, _('Flat Fee')),
        (BUDGET_TYPE_CONTINGENCY_FEE, _('Contingency Fee')),
        (BUDGET_TYPE_OTHER, _('Other Fee'))
    )
    budget_min = models.CharField(
        max_length=50,
        verbose_name=_('Budget Min'),
    )
    budget_max = models.CharField(
        max_length=50,
        verbose_name=_('Budget Max'),
    )
    budget_type = models.CharField(
        max_length=25,
        verbose_name=_('Budget type'),
        choices=BUDGET_TYPE_CHOICES,
        default=BUDGET_TYPE_HOURLY,
    )
    budget_detail = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Budget description'),
        help_text=_('Budget description')
    )
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Extra matter description')
    )
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = (
        (STATUS_ACTIVE, _('Active')),
        (STATUS_INACTIVE, _('Inactive'))
    )
    status = FSMField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name=_('Status')
    )
    status_modified = models.DateTimeField(
        default=timezone.now,
        help_text=_('Datetime when status was modified'),
        verbose_name=_('Status Modified')
    )
    currency = models.ForeignKey(
        Currencies,
        on_delete=models.PROTECT,
        default=1,
        verbose_name=_('Currency'),
        related_name='posted_matters'
    )
    is_hidden_for_client = models.BooleanField(
        default=False,
        verbose_name=_('Hidden for client')
    )
    is_hidden_for_attorney = models.BooleanField(
        default=False,
        verbose_name=_('Hidden for attorney')
    )

    @transition(
        field=status,
        source=STATUS_ACTIVE,
        target=STATUS_INACTIVE
    )
    def deactivate(self):
        self.status_modified = timezone.now()
        self.proposals.update(status=Proposal.STATUS_CLOSED_BY_CLIENT)

    @transition(
        field=status,
        source=STATUS_INACTIVE,
        target=STATUS_ACTIVE
    )
    def reactivate(self):
        self.status_modified = timezone.now()
        self.proposals.update(status=Proposal.STATUS_PENDING)


class Proposal(BaseModel):
    """
    Contains details of attorney proposals.
    Attributes:
        attorney (Attorney): link to Attorney submitting proposal
        rate (Decimal): Rate proposed by attorney
        description (Text): Proposal details submitted by attorney
        post (PostedMatter): Link to posted matter
        status (str): status of proposal can be
            pending
            accepted
            revoked
            chat
    """
    attorney = models.ForeignKey(
        'users.Attorney',
        on_delete=models.PROTECT,
        verbose_name=_('Attorney'),
        related_name='proposals'
    )
    rate = models.CharField(
        max_length=50,
        verbose_name=_('rate'),
    )
    RATE_TYPE_HOURLY = 'hourly'
    RATE_TYPE_FLAT = 'flat_fee'
    RATE_TYPE_CONTINGENCY_FEE = 'contingency_fee'
    RATE_TYPE_OTHER = 'other'

    RATE_TYPE_CHOICES = (
        (RATE_TYPE_HOURLY, _('Hourly')),
        (RATE_TYPE_FLAT, _('Flat Fee')),
        (RATE_TYPE_CONTINGENCY_FEE, _('Contingency Fee')),
        (RATE_TYPE_OTHER, _('Other Fee'))
    )
    rate_type = models.CharField(
        max_length=25,
        verbose_name=_('Rate type'),
        choices=RATE_TYPE_CHOICES,
        default=RATE_TYPE_HOURLY,
    )
    rate_detail = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Rate description'),
        help_text=_('Rate description')
    )
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Proposal description')
    )
    post = models.ForeignKey(
        PostedMatter,
        on_delete=models.DO_NOTHING,
        verbose_name='Posted Matter',
        related_name='proposals'
    )

    currency = models.ForeignKey(
        Currencies,
        on_delete=models.PROTECT,
        default=1,
        verbose_name=_('Currency'),
        related_name='proposals'
    )

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REVOKED = 'revoked'
    STATUS_CHAT = 'chat'
    STATUS_WITHDRAWN = 'withdrawn'
    STATUS_CLOSED_BY_CLIENT = 'closed by client'

    STATUS_CHOICES = (
        (STATUS_PENDING, _('Pending')),
        (STATUS_ACCEPTED, _('Accepted')),
        (STATUS_REVOKED, _('Revoked')),
        (STATUS_CHAT, _('Chat')),
        (STATUS_WITHDRAWN, _('withdrawn')),
        (STATUS_CLOSED_BY_CLIENT, _('closed by client')),
    )

    status = FSMField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name=_('Status')
    )
    status_modified = models.DateTimeField(
        default=timezone.now,
        help_text=_('Datetime when status was modified'),
        verbose_name=_('Status Modified')
    )
    is_hidden_for_client = models.BooleanField(
        default=False,
        verbose_name=_('Hidden for client')
    )
    is_hidden_for_attorney = models.BooleanField(
        default=False,
        verbose_name=_('Hidden for attorney')
    )
