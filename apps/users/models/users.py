import uuid

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from imagekit import models as imagekitmodels
from imagekit.processors import ResizeToFill, Transpose

from libs import utils

from apps.core.models import BaseModel
from apps.finance.models import CustomerProxy

from ..models import querysets
from .managers import AppUserManager

__all__ = [
    'AppUser',
    'UserStatistic',
    'AppUserHelperMixin',
]


def upload_user_avatar_to(instance, filename):
    """Upload user avatars to this folder.

    Returns:
        String. Generated path for image.

    """
    return 'users/avatars/{filename}'.format(
        filename=utils.get_random_filename(filename)
    )


class AppUser(BaseModel, AbstractBaseUser, PermissionsMixin):
    """Custom user model.

    Attributes:
        uuid (str):
            Used to make unique email unsubscribe link.
        first_name (str): first name
        middle_name (str): middle name - optional
        last_name (str): last name
        email (str): email (should be unique), this is our username field
        phone(str): Phone number
        avatar (file): user's avatar, cropped to fill 300x300 px
        is_staff (bool): designates whether the user can log into
            this admin site
        is_active (bool): designates whether this user should be
            treated as active
        active_subscription (SubscriptionProxy): link to active current
        subscription object
        date_joined (datetime): when user joined
        specialities (Speciality):
            This field has two meanings:
                In case of Attorney: it lists specialities of attorney
                In case of Client: it lists specialities client needs help with
        twofa (boolean): Flag for two factor authentication
        timezone (TimeZone): foreign key to TimeZone

    """
    # different possible in app user types
    USER_TYPE_ATTORNEY = 'attorney'
    USER_TYPE_PARALEGAL = 'paralegal'
    USER_TYPE_ENTERPRISE = 'enterprise'
    USER_TYPE_CLIENT = 'client'
    USER_TYPE_SUPPORT = 'support'
    USER_TYPE_STAFF = 'staff'

    USER_TYPES = (
        USER_TYPE_ATTORNEY,
        USER_TYPE_PARALEGAL,
        USER_TYPE_ENTERPRISE,
        USER_TYPE_CLIENT,
        USER_TYPE_SUPPORT,
        USER_TYPE_STAFF,
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=_('User uuid'),
        help_text=_(
            'Used to make unique user unsubscribe link'
        )
    )

    first_name = models.CharField(
        _('First name'),
        max_length=30,
    )

    middle_name = models.CharField(
        _('Middle name'),
        max_length=150,
        null=True,
        blank=True,
    )

    last_name = models.CharField(
        _('Last name'),
        max_length=150,
    )

    email = models.EmailField(
        _('E-mail address'),
        unique=True,
    )

    phone = models.CharField(
        max_length=128,
        verbose_name=_('Phone'),
        help_text=_('Phone number'),
        blank=True,
        null=True
    )

    date_joined = models.DateTimeField(
        _('Date joined'),
        default=timezone.now
    )

    is_staff = models.BooleanField(
        _('Staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'),
    )

    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    is_subscribed = models.BooleanField(
        _('Subscribed'),
        default=True,
        help_text=(
            'Designates whether the user subscribe email notification'
        )
    )

    active_subscription = models.ForeignKey(
        to='finance.SubscriptionProxy',
        verbose_name=_('Current active subscription'),
        on_delete=models.SET_NULL,
        related_name='appuser',
        null=True,
        blank=True,
        help_text=_(
            'Represents related to user current active stripe subscription'
        ),
    )

    avatar = imagekitmodels.ProcessedImageField(
        upload_to=upload_user_avatar_to,
        processors=[ResizeToFill(*settings.USER_AVATAR_SIZE), Transpose()],
        format='PNG',
        options={'quality': 100},
        null=True,
        blank=True
    )

    specialities = models.ManyToManyField(
        'Speciality',
        verbose_name=_('Specialities'),
        related_name='users'
    )

    twofa = models.BooleanField(
        _('Two Fator Authentication'),
        default=False,
    )

    onboarding = models.BooleanField(
        _('Onboarding process'),
        default=False,
    )

    timezone = models.ForeignKey(
        'users.Timezone',
        on_delete=models.SET_NULL,
        related_name='users',
        blank=True,
        null=True,
        default=None  # Set PST as default
    )

    objects = AppUserManager()

    # so authentication happens by email instead of username
    USERNAME_FIELD = 'email'

    # Make sure to exclude email from required fields if authentication
    # is done by email
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('AppUser')
        verbose_name_plural = _('AppUsers')

    def __str__(self):
        if self.full_name:
            return self.full_name
        return self.email

    @property
    def avatar_url(self):
        """Return the user's avatar"""
        if self.avatar == '[]' or self.avatar == '':
            return None
        elif self.avatar is None:
            return None
        return self.avatar.url

    @property
    def full_name(self):
        """Return the user's full name, if it is set."""
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return None

    @property
    def is_attorney(self):
        """Check if user is attorney or not.

        self.attorney is link to Attorney model defined in attorneys.py.

        """
        return hasattr(self, 'attorney')

    @property
    def is_client(self):
        """Check if user is client or not.

        self.client is link to Client model defined in clients.py.

        """
        return hasattr(self, 'client')

    @property
    def is_support(self):
        """Check if user is support or not.

        self.support is link to Support model defined in support.py.

        """
        return hasattr(self, 'support')

    @property
    def is_developer(self):
        """Is user is app developer. Used for permission checking.
        """
        admins = getattr(settings, 'ADMINS', [])
        admin_emails = [email for name, email in admins]
        admin_emails += ['root@root.ru']
        return self.email in admin_emails

    @property
    def is_paralegal(self):
        """Check if user is paralegal or not

        self.paralegal is link to Paralegal model defined in paralegal.py.

        """
        return hasattr(self, 'paralegal')

    @property
    def is_enterprise_admin(self):
        """Check if user is enterprise admin or not

        self.enterprise is link to Enterprise model defined in enterprise.py

        """
        return hasattr(self, 'owned_enterprise') and \
            self.owned_enterprise and \
            self.owned_enterprise.user_id == self.pk

    def is_enterprise_admin_of(self, enterprise_id):
        """Check if user is enterprise admin or not

        self.enterprise is link to Enterprise model defined in enterprise.py

        """
        return hasattr(self, 'owned_enterprise') and \
            self.owned_enterprise and \
            str(self.owned_enterprise.id) == enterprise_id

    @property
    def user_type(self):
        """Return user's type as str."""
        if self.is_client:
            return self.USER_TYPE_CLIENT
        elif self.is_enterprise_admin:
            return self.USER_TYPE_ENTERPRISE
        elif self.is_attorney:
            return self.USER_TYPE_ATTORNEY
        elif self.is_support:
            return self.USER_TYPE_SUPPORT
        elif self.is_paralegal:
            return self.USER_TYPE_PARALEGAL
        return self.USER_TYPE_STAFF

    @property
    def user_type_display(self):
        """Return user's type `display` value as str."""
        from ..models import Support

        # `support` user should be shown as `Paralegal` in frontend
        if self.is_support:
            return Support.DISPLAY_NAME
        return self.user_type

    @property
    def display_name(self):
        """Get user's display name."""
        if self.is_client:
            return self.client.display_name
        elif self.is_attorney:
            return self.attorney.display_name
        elif self.is_support:
            return self.support.display_name
        return self.full_name

    @cached_property
    def has_active_subscription(self) -> bool:
        """Check that user have active subscription"""
        return bool(self.active_subscription_id)

    @cached_property
    def customer(self):
        """Return related customer"""
        return CustomerProxy.objects.filter(subscriber=self).first()

    @property
    def deposit_account(self):
        """Get user's deposit account."""
        from ...finance.models import FinanceProfile
        try:
            return self.finance_profile.deposit_account
        except FinanceProfile.DoesNotExist:
            return None

    @property
    def plan_id(self):
        """Get user's plan_id"""
        try:
            return self.finance_profile.initial_plan.id
        except AttributeError:
            return None

    @property
    def subscribed(self):
        """Check if user subscribes or not"""
        canceled = True
        if self.customer:
            current_sub = self.customer.current_subscription
            if current_sub.status == 'canceled':
                canceled = False
            elif current_sub.status == 'active' and \
                    current_sub.cancel_at_period_end:
                canceled = False
        return canceled

    @property
    def expiration_date(self):
        """Check if user subscribes or not"""
        expiration_date = None
        from apps.finance.models import SubscriptionProxy

        if self.customer:
            current_sub = self.customer.current_subscription
            if current_sub.status == 'active' and \
                    current_sub.cancel_at_period_end:
                expiration_date = SubscriptionProxy.get_cancel_date(
                    current_sub
                )
        return expiration_date


class AppUserHelperMixin:
    """Common properties for Attorney, Clients and Support models."""

    def __str__(self):
        if hasattr(self, 'user'):
            return str(self.user)
        return 'None'

    def clean_user(self):
        """Check that user is not already a user of another type."""
        from . import Attorney, Client, Enterprise, Paralegal, Support

        if not hasattr(self, 'user'):
            return

        model_check_map = {
            Attorney: self.user.is_client or self.user.is_support,
            Paralegal: self.user.is_attorney or self.user.is_support,
            Enterprise: self.user.is_paralegal or self.user.is_support,
            Client: self.user.is_enterprise_admin or self.user.is_support,
            Support: self.user.is_attorney or self.user.is_client,
        }

        if model_check_map[self._meta.model]:
            raise ValidationError(_(
                f'User {self.user} is already attached to another user type'
            ))

    @property
    def email(self):
        """Get user's email."""
        return self.user.email

    @property
    def full_name(self):
        """Get user's full_name."""
        return self.user.full_name

    @property
    def display_name(self):
        """Get user's display name."""
        return self.full_name

    @cached_property
    def has_active_subscription(self) -> bool:
        """Check that user have active subscription"""
        return bool(self.user.active_subscription_id)

    @cached_property
    def customer(self):
        """Return related customer."""
        return CustomerProxy.objects.filter(subscriber_id=self.pk).first()

    @property
    def deposit_account(self):
        """Get user's deposit account."""
        return self.user.deposit_account


class UserStatistic(BaseModel):
    """This model represents user statistics.

    It used to keep track of different user statistics, like amount of
    converted leads or opportunities for period of time.

    Attributes:
        user (AppUser): Link to owner of statistic(user itself)
        tag (str):
            Identifier of statistic or in other words type of statistic,
            used for searching
        count (int):
            Used to keep track of amount of statistic(for example for
            20th september user had 17 opportunities)

    """

    user = models.ForeignKey(
        'users.AppUser',
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='statistics'
    )

    # Opportunities is topics that was created by users in attorney's
    # jurisdiction and have same category's specialty or contains keywords in
    # title or in first post same as attorney's.
    TAG_OPPORTUNITIES = 'opportunities'
    TAG_OPEN_MATTER = 'open_matter'
    TAG_REFERRED_MATTER = 'referred_matter'
    TAG_CLOSE_MATTER = 'close_matter'
    TAG_ACTIVE_LEAD = 'active_lead'
    # Converted lead is a lead that was mentioned in matter creation.
    TAG_CONVERTED_LEAD = 'converted_lead'
    TAGS = (
        (TAG_OPPORTUNITIES, _('Opportunities')),
        # (TAG_ACTIVE_MATTER, _('Active matter')),
        (TAG_OPEN_MATTER, _('Open matter')),
        (TAG_REFERRED_MATTER, _('Referred matter')),
        (TAG_CLOSE_MATTER, _('Close matter')),
        (TAG_ACTIVE_LEAD, _('Active lead')),
        (TAG_CONVERTED_LEAD, _('Converted lead')),
    )

    tag = models.CharField(
        max_length=50,
        choices=TAGS,
        verbose_name=_('Tag'),
        help_text=_('Identifier of statistic'),
    )

    count = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Count'),
        help_text=_('Count'),
    )

    objects = querysets.UserStatisticsQuerySet.as_manager()

    class Meta:
        verbose_name = _('User statistics')
        verbose_name_plural = _('User statistics')
        indexes = [
            models.Index(fields=('user', 'created',)),
        ]

    def __str__(self):
        return (
            f'Stats for {self.user}. Tag: {self.tag}, Count: {self.count}, '
            f'Date: {self.created}'
        )
