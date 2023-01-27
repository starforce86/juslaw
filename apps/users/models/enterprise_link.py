from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

from .. import notifications
from .users import AppUser


class Member(BaseModel):
    """ Model defines Member information of enterprise

    It describes memeber email and type

    Examples:
        test@test.com
        attorney

    Attributes:
        email(str): email of member
        type(str): user type of memeber
    """

    email = models.EmailField(
        _('Enterprise member email address'),
    )

    USER_TYPE_ATTORNEY = 'attorney'
    USER_TYPE_PARALEGAL = 'paralegal'
    USER_TYPES = (
        (USER_TYPE_ATTORNEY, _('Attorney')),
        (USER_TYPE_PARALEGAL, _('Paralegal')),
    )

    type = models.CharField(
        max_length=10,
        default=USER_TYPE_ATTORNEY,
        choices=USER_TYPES,
        verbose_name=_('Type of member')
    )

    class Meta:
        verbose_name = _('Member')
        verbose_name_plural = _('Members')

    def __str__(self):
        return self.email

    def _send_invitation(self, enterprise):
        if not AppUser.objects.filter(email__iexact=self.email).exists():
            notifications.EnterpriseMemberInvitationNotification(
                member=self,
                enterprise=enterprise
            ).send()
