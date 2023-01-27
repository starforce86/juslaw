from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from imagekit import models as imagekitmodels
from imagekit.processors import ResizeToFill, Transpose

from libs import utils

from apps.users.models.utils.verification import VerifiedRegistration

from . import querysets
from .users import AppUserHelperMixin


def upload_user_avatar_to(instance, filename):
    """Upload user avatars to this folder.

    Returns:
        String. Generated path for image.

    """
    return 'users/avatars/{filename}'.format(
        filename=utils.get_random_filename(filename)
    )


class Enterprise(AppUserHelperMixin, VerifiedRegistration):
    """Model defines information about enterprise.

    Model describes enterprise's firm size, firm location, members
    and extra information about enterprise.

    Notes:

    Attributes:
        user (AppUser): Relation to AppUser
        role(str): Specify Your Role
        verification_status (str):
            Verification_status of enterprise, there three statuses:
                not_verified - Default on submission
                approved - Approved by admins
                denied - Denied by admins
        featured(bool):
            If enterprise has Premium subscription it becomes featured
            enterprise on clients search
        followers(AppUser):
            Users that follow enterprise. They will get notifications about
            enterprise activity
        firm_name(str): Name of firm where enterprise is located
        firm_size(str): Size of firm
        firm_locations (dict):
            Name of country, state, city, address, zip code where enterprise is
            located
        team_members(Member): List of members in enterprise
    """
    user = models.OneToOneField(
        'users.AppUser',
        primary_key=True,
        on_delete=models.PROTECT,
        verbose_name=_('User'),
        related_name='enterprise'
    )

    team_logo = imagekitmodels.ProcessedImageField(
        upload_to=upload_user_avatar_to,
        processors=[ResizeToFill(*settings.USER_AVATAR_SIZE), Transpose()],
        format='PNG',
        options={'quality': 100},
        null=True,
        blank=True
    )

    role = models.CharField(
        max_length=20,
        verbose_name=_('Enterprise Role'),
        help_text=_("Enterprise Role")
    )

    followers = models.ManyToManyField(
        'users.AppUser',
        verbose_name=_('Followers'),
        related_name='followed_enterprise'
    )

    featured = models.BooleanField(
        default=False,
        verbose_name=_('Is featured')
    )

    # Location

    firm_name = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name=_('Firm name'),
        help_text=_('Firm Name')
    )

    firm_size = models.ForeignKey(
        'FirmSize',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enterprise',
        verbose_name=_('Firm size'),
        help_text=_('Firm size'),
    )

    firm_locations = models.ManyToManyField(
        'FirmLocation',
        related_name='enterprise',
        verbose_name=_('Firm Location'),
        help_text=_(
            'Country, State(s), Address(s), City(s), Zipcode '
            'of enterprise\'s Firm'
        )
    )

    team_members = models.ManyToManyField(
        'Member',
        related_name='enterprise',
        verbose_name=_('Team Members'),
        help_text=_(
            'Email, User type of enterprise members'
        )
    )

    objects = querysets.EnterpriseQuerySet.as_manager()

    class Meta:
        verbose_name = _('Enterprise')
        verbose_name_plural = _('Enterprise')

    def post_verify_by_admin_hook(self, **kwargs):
        """Separate hook to add custom `verification` business logic.

        After successful user verification by admin send
        `enterprise_verified` signal.

        """
        from ..signals import enterprise_verified
        enterprise_verified.send(
            sender=self.user._meta.model,
            instance=self.user
        )
