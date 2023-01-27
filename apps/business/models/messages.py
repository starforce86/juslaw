from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

from . import Attachment
from .matter import Matter
from .querysets import MatterCommentQuerySet, MatterPostQuerySet


class MatterPost(BaseModel):
    """Post model in Matter app.

    Posts are thread between attorney and client attached to matter.

    Attributes:
        matter (Matter): Foreign key to Matter model.
        title (str): title of Topic
        comment_count (int): Amount of post topic
        last_comment (MatterPost): Link to the last post in topic
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time
        participants (AppUser): Invited users by creator
        attachments (Attachment): Attachments for the mattertopic
        seen (bool): If the matter comment has been read or not
        seen_by_client (bool): If the matter comment has been read
            or not by client

    """

    matter = models.ForeignKey(
        'Matter',
        on_delete=models.CASCADE,
        related_name='posts',
        null=True,
    )
    title = models.CharField(
        _('Title'),
        max_length=255,
        null=True
    )
    comment_count = models.IntegerField(
        _('Comment count'),
        default=0,
    )
    last_comment = models.ForeignKey(
        'MatterComment',
        verbose_name=_('Last Comment'),
        on_delete=models.SET_NULL,
        related_name='last_comment_on_post',
        null=True,
        blank=True,
    )
    participants = models.ManyToManyField(
        to='users.AppUser',
        verbose_name=_('Participants'),
        related_name='matter_topic',
    )
    attachments = models.ManyToManyField(
        to=Attachment,
        verbose_name=_('Attachments'),
        related_name='matter_topic'
    )
    seen = models.BooleanField(
        default=False,
        verbose_name=_('Seen'),
        help_text=_('If the matter topic has been read or not')
    )
    seen_by_client = models.BooleanField(
        default=False,
        verbose_name=_('Seen'),
        help_text=_('If the matter topic has been read or not by client')
    )

    @property
    def unread_comment_count(self):
        return self.comments.filter(seen=False).count()

    @property
    def unread_comment_by_client_count(self):
        return self.comments.filter(seen_by_client=False).count()

    objects = MatterPostQuerySet.as_manager()

    class Meta:
        verbose_name = _('Matter Message Post')
        verbose_name_plural = _('Matter Message Posts')


class MatterComment(BaseModel):
    """Comment model in Matter app.

    Comments in matters represent messages between
    attorney and client on certain
    post related to matter.

    Attributes:
        post (MatterTopic): link to a post in which comment is placed
        author (AppUser): link to post author.
        text (text): text of an offer
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time
        seen (bool): If the matter comment has been read or not
        seen_by_client (bool): If the matter comment has been read
            or not by client

    """
    seen = models.BooleanField(
        default=False,
        verbose_name=_('Seen'),
        help_text=_('If the matter comment has been read or not')
    )
    seen_by_client = models.BooleanField(
        default=False,
        verbose_name=_('Seen'),
        help_text=_('If the matter topic has been read or not by client')
    )
    post = models.ForeignKey(
        'MatterPost',
        on_delete=models.CASCADE,
        verbose_name=_('Post'),
        related_name='comments',
    )
    author = models.ForeignKey(
        'users.AppUser',
        on_delete=models.PROTECT,
        verbose_name=_('Author'),
        related_name='matter_comments',
    )
    participants = models.ManyToManyField(
        to='users.AppUser',
        verbose_name=_('Participants'),
        related_name='matter_comments_pariticipants',
    )
    deleted_participants = models.ManyToManyField(
        to='users.AppUser',
        verbose_name=_('Deleted Participants'),
        related_name='matter_comments_deleted_pariticipants',
    )
    text = models.TextField(
        _('Text of the post'),
    )
    attachments = models.ManyToManyField(
        to=Attachment,
        verbose_name=_('Attachments'),
        related_name='matter_comments'
    )

    objects = MatterCommentQuerySet.as_manager()

    class Meta:
        verbose_name = _('Matter Message Comment')
        verbose_name_plural = _('Matter Message Comments')

    def clean_author(self):
        """Check that author is related to topics matter."""
        if not Matter.objects.available_for_user(user=self.author).filter(
            topics=self.pk
        ).exists():
            raise ValidationError('Author is not related to matter.')

    @property
    def matter(self):
        """Get related matter from `topic`."""
        return self.post.matter
