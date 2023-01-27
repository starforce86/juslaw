import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ckeditor_uploader.fields import RichTextUploadingField
from imagekit.models import ImageSpecField
from pilkit.processors import ResizeToFill, Transpose

from ..chats.models import AbstractChat
from ..core.models import BaseModel
from ..documents.models.resources import upload_documents_to
from .querysets import ChatQuerySet


def upload_attorney_post_image_to(instance, filename):
    """Upload attorney post image to this `attorney_post` folder.

    Returns:
        String. Generated path for image.

    """
    return 'public/attorney_post/{folder}/{filename}'.format(
        folder=uuid.uuid4(),
        filename=filename
    )


class AttorneyPost(BaseModel):
    """Model defines posts made by attorney in social app.

    More advanced version of posts, which can only be created by attorneys.

    Attributes:
        author (Attorney): author of post
        title (str): Post's title
        image (file): Image of post
        image_thumbnail (file):
            Preview of post's image, generated automatically
        body (str): post content
        body_preview (str): Text preview of post
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """

    author = models.ForeignKey(
        'users.Attorney',
        related_name='posts',
        on_delete=models.PROTECT
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Post title'),
    )

    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=upload_attorney_post_image_to,
        verbose_name=_('Post Image'),
        help_text=_('Post Image'),
    )

    image_thumbnail = ImageSpecField(
        source='image',
        processors=[
            ResizeToFill(*settings.ATTORNEY_POST_THUMBNAIL_SIZE),
            Transpose()
        ],
        format='PNG',
        options={'quality': 100},
    )

    body = RichTextUploadingField(
        config_name='default',
        verbose_name=_('Body'),
        help_text=_('Content of post')
    )

    body_preview = models.TextField(
        max_length=150,
        verbose_name=_('Preview'),
        help_text=_('Text preview of post')
    )

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def __str__(self):
        return f'Post ({self.pk}): {self.title[:50]}'


class SingleChatParticipants(BaseModel):
    appuser = models.ForeignKey(
        'users.AppUser',
        related_name='single_chat_participants',
        verbose_name=_('User'),
        on_delete=models.CASCADE
    )
    chat = models.ForeignKey(
        'Chats',
        related_name='single_chat_participants',
        verbose_name=_('User'),
        on_delete=models.CASCADE
    )
    is_favorite = models.BooleanField(
        default=False,
        verbose_name=_('Favorite')
    )


class Chats(AbstractChat):
    """
    Chat between the appUser can be between any kind of app users.
    Attributes:
        chat_channel (str): id of chat in firestore
        participants (AppUsers): two participants of the chat can be two no
                                 more no less
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time
        is_group (Boolean): determines if its a group chat or direct(1v1) chat
    """
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        null=True,
        blank=True
    )
    chat_channel = models.UUIDField(
        unique=True,
        editable=False,
        default=uuid.uuid4,
        verbose_name=_('Chat channel ID'),
    )

    participants = models.ManyToManyField(
        'users.AppUser',
        verbose_name=_('Participants'),
        related_name='chats',
        related_query_name="%(app_label)s_%(class)ss",
        through='SingleChatParticipants'
    )
    is_group = models.BooleanField(default=False)

    objects = ChatQuerySet.as_manager()

    class Meta:
        verbose_name = _('Chat')
        verbose_name_plural = _('Chats')


class Message(BaseModel):
    """Model containing chat messages"""
    author = models.ForeignKey(
        'users.AppUser',
        on_delete=models.CASCADE,
        verbose_name=_('Author'),
        related_name='chat_messages',
    )
    chat = models.ForeignKey(
        'Chats',
        on_delete=models.CASCADE,
        related_name='messages',
    )
    type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_('Message Type')
    )
    timestamp1 = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Timestamp')
    )
    text = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Message Text')
    )


class MessageAttachment(BaseModel):
    """Model for message attachments"""
    message = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        related_name='attachment'
    )
    file = models.FileField(
        max_length=255,
        upload_to=upload_documents_to,
        verbose_name=_('File'),
        help_text=_("Document's file"),
    )
