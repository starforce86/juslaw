import mimetypes
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from ...core.models import BaseModel
from . import Attachment, querysets

__all__ = (
    'Activity',
    'Note',
    'VoiceConsent',
    'MatterSharedWith'
)


def upload_voice_consents_to(instance, filename: str) -> str:
    """Upload voice consent to voice consents folder.

    Args:
        instance (VoiceConsent): instance of voice_consent model
        filename (str): file name of voice consent's file

    Returns:
        str: Generated path for voice consent's file.

    """
    return 'public/voice_consents/{folder}/{filename}'.format(
        folder=uuid.uuid4(),
        filename=filename
    )


class Activity(BaseModel):
    """Activity model

    This model represents the events ('activities') that occurred in the frame
    of this matter (for example: `Monthly Invoice Sent`, `Term sheet provided
    to Abby` and etc).

    Attributes:
        matter (Matter): is the matter for which activity was made
        title (str): the name/title of made activity
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """
    matter = models.ForeignKey(
        'Matter',
        # activity has no meaning without a corresponding matter
        on_delete=models.CASCADE,
        related_name='activities'
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Title which describes current activity')
    )
    user = models.ForeignKey(
        'users.AppUser',
        on_delete=models.CASCADE,
        related_name='activities',
        null=True,
        blank=True
    )

    ACTIVITY_TYPE_MESSAGE = 'message'
    ACTIVITY_TYPE_DOCUMENT = 'document'
    ACTIVITY_TYPE_NOTE = 'note'
    ACTIVITY_TYPE_INVOICE = 'invoice'
    ACTIVITY_TYPE_BILLING_ITEM = 'billing_item'

    ACTIVITY_TYPE_CHOICES = (
        (ACTIVITY_TYPE_MESSAGE, _('Message')),
        (ACTIVITY_TYPE_DOCUMENT, _('Document')),
        (ACTIVITY_TYPE_NOTE, _('Note')),
        (ACTIVITY_TYPE_INVOICE, _('Invoice')),
        (ACTIVITY_TYPE_BILLING_ITEM, _('Billing item')),
    )

    type = models.CharField(
        max_length=25,
        verbose_name=_('Activity type'),
        choices=ACTIVITY_TYPE_CHOICES,
        null=True,
        blank=True,
        default=None,
    )

    objects = querysets.MatterRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = _('Activity')
        verbose_name_plural = _('Activities')

    def __str__(self):
        return self.title


class Note(BaseModel):
    """Note model

    Attributes:
        matter (Matter): is a matter to which user added a note (some info
        for him)
        title (str): summary shorten note name
        text (text): full note text
        created_by (AppUser): a note author
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """
    matter = models.ForeignKey(
        'Matter',
        on_delete=models.CASCADE,
        related_name='notes',
    )
    client = models.ForeignKey(
        'users.AppUser',
        on_delete=models.CASCADE,
        related_name='notes_client',
        null=True
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
    )
    text = models.TextField(
        verbose_name=_('Text'),
    )
    created_by = models.ForeignKey(
        'users.AppUser',
        verbose_name=_('Created by'),
        help_text=_('AppUser created the note'),
        related_name='notes',
        on_delete=models.PROTECT
    )
    attachments = models.ManyToManyField(
        to=Attachment,
        verbose_name=_('Attachments'),
        related_name='notes'
    )

    objects = querysets.NoteQuerySet.as_manager()

    class Meta:
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')

    def __str__(self):
        return self.title


class VoiceConsent(BaseModel):
    """VoiceConsent model.

    This model represents voice consent entries. It used when client after it
    looked over matters documents, wants to give voice consent.

    Attributes:
        matter (Matter): Link to matter, to which consent was given
        title (str): Title of voice consent
        file (file): Voice consent's file
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """

    matter = models.ForeignKey(
        to='Matter',
        on_delete=models.CASCADE,
        related_name='voice_consents'
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
    )
    file = models.FileField(
        max_length=255,
        upload_to=upload_voice_consents_to,
        verbose_name=_('File'),
        help_text=_("Voice consent's file"),
    )

    objects = querysets.VoiceConsentQuerySet.as_manager()

    class Meta:
        verbose_name = _('Voice Consent')
        verbose_name_plural = _('Voice Consents')
        unique_together = ('matter', 'title')

    def __str__(self):
        return f'Voice Consent ({self.pk}) @ {self.matter}'

    def clean_file(self):
        """Check that file is an audio file."""
        mime_type = mimetypes.guess_type(str(self.file))[0]
        if mime_type not in settings.AUDIO_MIME_TYPES:
            raise ValidationError(
                "Voice consent's file must be an audio file"
            )


class MatterSharedWith(BaseModel):
    """MatterSharedWith model.

    Defines users, which have access to not owned by them matters and all
    permissions for it.

    Business case: original matter attorney may invite another users to his
    matter so they could help him (attorneys or support users).

    Attributes:
        matter (Matter): Link to matter, which is shared with attorney
        user (AppUser): Link to user with which matter is shared
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """
    matter = models.ForeignKey(
        to='Matter',
        on_delete=models.CASCADE,
        related_name='shared_links',
        verbose_name=_('Matter'),
        help_text=_('Matter that was shared with attorney')
    )
    user = models.ForeignKey(
        to='users.AppUser',
        on_delete=models.CASCADE,
        related_name='shared_links',
        verbose_name=_('User'),
        help_text=_('User with which matter was shared')
    )

    objects = querysets.MatterSharedWithQuerySet.as_manager()

    class Meta:
        verbose_name = _('Matter Shared With')
        verbose_name_plural = _('Matters Shared With')
        unique_together = ('matter', 'user')

    def __str__(self):
        return f'Shared with ({self.pk}) @ {self.matter}'


class InvoiceActivity(BaseModel):
    """Invoice Activity model

    This model represents the events ('activities') that occurred in the frame
    of this invoice (for example: `Monthly Invoice Sent` and etc).

    Attributes:
        activity (str): the name/title of made activity
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """
    activity = models.CharField(
        max_length=255,
        null=True,
        verbose_name=_('Activity'),
        help_text=_('Title which describes current activity')
    )

    objects = querysets.MatterRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = _('InvoiceActivity')
        verbose_name_plural = _('InvoiceActivities')

    def __str__(self):
        return self.activity


class InvoiceLog(BaseModel):
    """Invoice Log model

    This model represents the events ('log') that occurred in the frame
    of this invoice (for example: `200 POST /v1/incoice/in_1ITVSK34FJV/send`
    and etc).

    Attributes:
        status (str): the stripe API response code
        method (str): the stripe API method
        log (str): the stripe API logs
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """
    status = models.CharField(
        max_length=20,
        null=True,
        verbose_name=_('Status'),
    )

    method = models.CharField(
        max_length=10,
        null=True,
        verbose_name=_('Method')
    )

    log = models.CharField(
        max_length=255,
        null=True,
        verbose_name=_('Logs'),
        help_text=_('Title which describes current log'),
    )

    objects = querysets.MatterRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = _('InvoiceLog')
        verbose_name_plural = _('InvoiceLogs')

    def __str__(self):
        return self.log
