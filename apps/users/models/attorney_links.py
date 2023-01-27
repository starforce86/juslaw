import os
import uuid

from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.users.validators import validate_activity_year

from .attorneys import Attorney


def upload_registration_attachments_to(instance, filename: str) -> str:
    """Upload attorneys' `documents` for registration folder.

    Args:
        instance (Document): instance of attorney
        filename (str): file name of document's file

    Returns:
        str: Generated path for document's file.

    """
    template = 'public/attorney_registration_attachments/{folder}/{filename}'
    return template.format(
        folder=uuid.uuid4(),
        filename=filename
    )


class AttorneyEducation(BaseModel):
    """Defines many to many relationship between attorney and University.

    University is a place where attorney studied law and graduated from

    Attributes:
        university (University): University, where attorney studied law
        attorney (Attorney): relation to Attorney
        year(int): Year of graduation
    """
    university = models.ForeignKey(
        'AttorneyUniversity',
        verbose_name=_('University'),
        related_name='attorney_education',
        on_delete=models.PROTECT
    )
    attorney = models.ForeignKey(
        'Attorney',
        verbose_name=_('Attorney'),
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
        verbose_name = _('Attorney\'s education')
        verbose_name_plural = _('Attorneys\' education')


class UniversityQuerySet(QuerySet):
    """QuerySet class `University` model."""

    def verified_universities(self):
        """Get all verified universities.

        Verified university is university where at least one verified attorney
        studied.

        """
        filter_params = {
            'attorney_education__attorney__verification_status':
                Attorney.VERIFICATION_APPROVED
        }
        return self.filter(**filter_params).distinct()


class AttorneyUniversity(BaseModel):
    """Model defines University.

    It describes university where attorneys graduated from

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


class AttorneyRegistrationAttachment(BaseModel):
    """Attachment file added by attorney on registration.

    Attributes:
        attorney (Attorney): Link to attorney
        attachment (file): Added by attorney on registration

    """
    attorney = models.ForeignKey(
        'Attorney',
        verbose_name=_('Attorney'),
        related_name='registration_attachments',
        on_delete=models.CASCADE
    )

    attachment = models.FileField(
        max_length=255,
        upload_to=upload_registration_attachments_to,
        verbose_name=_('Attachment file'),
        help_text=_(
            'Extra file attached by attorney on registration'
        ),
    )

    class Meta:
        verbose_name = _("Attorney's registration attachment")
        verbose_name_plural = _("Attorney's registration attachments")

    @property
    def attachment_file_name(self):
        """Get attachment's file name."""
        return os.path.basename(self.attachment.name)

    def __str__(self):
        return (
            f"Attorney {self.attorney.display_name}'s "
            f'attachment: {self.attachment_file_name}'
        )
