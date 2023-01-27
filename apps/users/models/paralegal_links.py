import os
import uuid

from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.users.validators import validate_activity_year

from .paralegal import Paralegal


def upload_registration_attachments_to(instance, filename: str) -> str:
    """Upload paralegal' `documents` for registration folder.

    Args:
        instance (Document): instance of paralegal
        filename (str): file name of document's file

    Returns:
        str: Generated path for document's file.

    """
    template = 'public/paralegal_registration_attachments/{folder}/{filename}'
    return template.format(
        folder=uuid.uuid4(),
        filename=filename
    )


class ParalegalEducation(BaseModel):
    """Defines many to many relationship between paralegal and University.

    University is a place where paralegal studied law and graduated from

    Attributes:
        university (University): University, where paralegal studied law
        paralegal (Paralegal): relation to Paralegal
        year(int): Year of graduation
    """
    university = models.ForeignKey(
        'ParalegalUniversity',
        verbose_name=_('University'),
        related_name='paralegal_education',
        on_delete=models.PROTECT
    )
    paralegal = models.ForeignKey(
        'Paralegal',
        verbose_name=_('Paralegal'),
        related_name='education',
        on_delete=models.PROTECT
    )

    year = models.IntegerField(
        verbose_name=_('Year'),
        validators=(
            validate_activity_year,
        )
    )

    class Meta:
        verbose_name = _('Paralegal\'s education')
        verbose_name_plural = _('Paralegals\' education')


class UniversityQuerySet(QuerySet):
    """QuerySet class `University` model."""

    def verified_universities(self):
        """Get all verified universities.

        Verified university is university where at least one verified paralegal
        studied.

        """
        filter_params = {
            'paralegal_education__paralegal__verification_status':
                Paralegal.VERIFICATION_APPROVED
        }
        return self.filter(**filter_params).distinct()


class ParalegalUniversity(BaseModel):
    """Model defines University.

    It describes university where paralegals graduated from

    Attributes:
        title(str): Name of university
    """

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        unique=True,
    )

    objects = UniversityQuerySet.as_manager()

    class Meta:
        verbose_name = _('University')
        verbose_name_plural = _('Universities')

    def __str__(self):
        return self.title


class ParalegalRegistrationAttachment(BaseModel):
    """Attachment file added by paralegal on registration.

    Attributes:
        paralegal (Paralegal): Link to paralegal
        attachment (file): Added by paralegal on registration

    """
    paralegal = models.ForeignKey(
        'Paralegal',
        verbose_name=_('Paralegal'),
        related_name='registration_attachments',
        on_delete=models.CASCADE
    )

    attachment = models.FileField(
        max_length=255,
        upload_to=upload_registration_attachments_to,
        verbose_name=_('Attachment file'),
        help_text=_(
            'Extra file attached by paralegal on registration'
        ),
    )

    class Meta:
        verbose_name = _("Paralegal's registration attachment")
        verbose_name_plural = _("Paralegal's registration attachments")

    @property
    def attachment_file_name(self):
        """Get attachment's file name."""
        return os.path.basename(self.attachment.name)

    def __str__(self):
        return (
            f"Paralegal {self.paralegal.display_name}'s "
            f'attachment: {self.attachment_file_name}'
        )
