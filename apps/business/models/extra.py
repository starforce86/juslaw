import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from ...core.models import BaseModel
from .querysets import VideoCallQuerySet

__all__ = (
    'Attachment',
    'Stage',
    'ChecklistEntry',
    'VideoCall',
)

from ...documents.models.resources import upload_documents_to


class Attachment(BaseModel):
    """Model represents attachments(file) in library.

    Attributes:
`       mime_type (str): Mime type of file
        file (file): Document's file in s3 storage

    """

    mime_type = models.CharField(
        max_length=255,
        verbose_name=_('Mime type'),
        help_text=_('Mime type of file')
    )

    file = models.FileField(
        max_length=255,
        upload_to=upload_documents_to,
        verbose_name=_('File'),
        help_text=_("Document's file"),
    )

    def __str__(self):
        return self.file.name


class Stage(BaseModel):
    """Model defines attorneys custom stages of matters.

    Attorney can create for itself several custom stages and set them to it's
    matters.

    Attributes:
        attorney (Attorney): Link to owner of stage (attorney)
        title (str): title of stage
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time
    """

    attorney = models.ForeignKey(
        'users.Attorney',
        on_delete=models.PROTECT,
        verbose_name=_('Attorney'),
        related_name='stages'
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
    )

    class Meta:
        verbose_name = _('Stage')
        verbose_name_plural = _('Stages')

    def __str__(self):
        return self.title

    @classmethod
    def create_default_stages(cls, attorney):
        cls.objects.create(attorney=attorney, title='Discovery')
        cls.objects.create(attorney=attorney, title='Trial')


class ChecklistEntry(BaseModel):
    """ChecklistEntry model.

    This model represents checklist entries. It used when attorney trying to
    close matter. Attorney review it's checklist, and if all entries checked
    (on front-end part), attorney can close matter.

    Attributes:
        attorney (Attorney): Owner of checklist entry
        description (str): Description of checklist

    """
    attorney = models.ForeignKey(
        'users.Attorney',
        verbose_name=_('Attorney'),
        related_name='checklist',
        on_delete=models.PROTECT
    )

    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Description of checklist')
    )

    class Meta:
        verbose_name = _('Checklist Entry')
        verbose_name_plural = _('Checklist Entries')
        unique_together = ('attorney', 'description')

    def __str__(self):
        return self.description

    def clean_description(self):
        """Check that check list entry has unique description."""
        duplicate = self.__class__.objects.filter(
            description=self.description, attorney_id=self.attorney_id,
        ).exclude(pk=self.pk)
        if duplicate.exists():
            raise ValidationError(
                f'Entry with same description:`{self.description}` '
                f'is already exist'
            )


class VideoCall(BaseModel):
    """VideoCall model.

    This model represents video calls in jitsi. Attorney or client can create
    a video call, after it's creation all invited users will receive
    notifications.

    Attributes:
        call_id (str):
            Id of meeting in jitsi(it used to create a link)
            Example:
                https://meet.jit.si/{call_id}
        participants (AppUser): Invited users by creator

    """
    VIDEO_CALL_BASE_URL = 'https://meet.jit.si/'
    MAX_PARTICIPANTS_COUNT = 10

    call_id = models.UUIDField(
        editable=False,
        unique=True,
        default=uuid.uuid4,
        verbose_name=_('Id of call'),
        help_text=_('Id of call(name of room in jitsi)'),
    )

    participants = models.ManyToManyField(
        'users.AppUser',
        verbose_name=_('Participants'),
        related_name='video_calls',
    )

    objects = VideoCallQuerySet.as_manager()

    class Meta:
        verbose_name = _('Video Call')
        verbose_name_plural = _('Video Calls')

    def __str__(self):
        return f'Video call @ {self.call_id}'

    @property
    def call_url(self) -> str:
        """Get full url of call."""
        return (
            f'{self.VIDEO_CALL_BASE_URL}{self.call_id}'
            # this part id added so mobiles wouldn't ask to install jitsi
            '#config.disableDeepLinking=true'
        )


class Referral(BaseModel):
    """Referral model

    This model represents the matter referral request from other attorney

    Attributes:
        attorney (Attorney): Referred attorney
        message (str): Message from attorney

    """
    attorney = models.ForeignKey(
        'users.Attorney',
        verbose_name=_('Attorney'),
        related_name='referral',
        on_delete=models.PROTECT
    )
    message = models.TextField(
        verbose_name=_('Message'),
        help_text=_('Referral message'),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Referral')
        verbose_name_plural = _('Referrals')

    def __str__(self):
        return f'Referred from {self.attorney}'


class PaymentMethods(BaseModel):
    """PaymentMethods model

    This model represents available payment methods of invoice

    Attributes:
        title (str): title of payment methods

    """
    title = models.CharField(
        max_length=30,
        verbose_name=_('Title'),
        help_text=_('Payment methods'),
    )

    class Meta:
        verbose_name = _('PaymentMethod')
        verbose_name_plural = _('PaymentMethods')

    def __str__(self):
        return self.title
