import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ckeditor_uploader.fields import RichTextUploadingField
from imagekit.models import ImageSpecField
from pilkit.processors import ResizeToFill, Transpose
from taggit.managers import TaggableManager

from apps.core.models import BaseModel

from .links import NewsCategoriesLink, NewsTagLink
from .querysets import NewsQuerySet


def upload_news_image_to(instance, filename):
    """Upload news image to this `news` folder.

    Returns:
        String. Generated path for image.

    """
    return 'public/news/{folder}/{filename}'.format(
        folder=uuid.uuid4(),
        filename=filename
    )


class News(BaseModel):
    """Model defines news.

    In admin panel, staff users, able to create news for app users to read.

    Attributes:
        title (str): News title
        image (file) image of news
        image_thumbnail (file):
            thumbnail of news(resized `image`), generated automatically
        description (str): Description or news content
        tags (NewsTagLink): tags of news
        categories (NewsCategoriesLink): categories of news

    """

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('News title'),
    )

    image = models.ImageField(
        upload_to=upload_news_image_to,
        verbose_name=_('Image'),
        help_text=_('News image'),
    )

    image_thumbnail = ImageSpecField(
        source='image',
        processors=[ResizeToFill(*settings.NEWS_THUMBNAIL_SIZE), Transpose()],
        format='PNG',
        options={'quality': 100},
    )
    author = models.ForeignKey(
        'users.AppUser',
        on_delete=models.CASCADE,
        verbose_name=_('Author'),
        related_name='news',
        null=True
    )

    description = RichTextUploadingField(
        config_name='default',
        verbose_name=_('Description'),
        help_text=_('Content of news')
    )

    tags = TaggableManager(
        blank=True,
        through=NewsTagLink
    )
    categories = TaggableManager(
        verbose_name=_('Categories'),
        help_text=_('A comma-separated list of categories.'),
        through=NewsCategoriesLink
    )

    objects = NewsQuerySet.as_manager()

    class Meta:
        verbose_name = _('News')
        verbose_name_plural = _('News')

    def __str__(self):
        return f'News ({self.pk}): {self.title[:50]}'
