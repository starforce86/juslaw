import mimetypes
import uuid

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

from . import querysets

__all__ = (
    'Resource',
    'Folder',
    'Document',
)


def upload_documents_to(instance, filename: str) -> str:
    """Upload instance's `documents` to documents or templates folder.

    Args:
        instance (Document): instance of document model
        filename (str): file name of document's file

    Returns:
        str: Generated path for document's file.

    """
    document_path = f'{uuid.uuid4()}/{filename}'

    if getattr(instance, 'is_global_template', None):
        return f'public/templates/{document_path}'
    return f'documents/{document_path}'


class Resource(BaseModel):
    """Common model for resources.

    Attributes:
        owner (AppUser):
            if it's personal folder, when it user itself
            if it's matter related folder, when it matter's attorney
        matter (Matter): relation to matter
        parent (Folder): Shows if resource is inside other folder
        title (str): Title of resource
        is_template (bool): Is a template resource

    """
    owner = models.ForeignKey(
        'users.AppUser',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_('Owner'),
        related_name='%(class)ss',
        related_query_name="%(app_label)s_%(class)ss",
    )

    matter = models.ForeignKey(
        'business.Matter',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_('Matter'),
        related_name='%(class)ss',
        related_query_name="%(app_label)s_%(class)ss",
    )

    client = models.ForeignKey(
        'users.AppUser',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_('client'),
        related_name='%(class)s',
        related_query_name="%(app_label)s_%(class)s",
    )

    parent = models.ForeignKey(
        'documents.Folder',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_('Parent'),
        related_name='%(class)ss',
        related_query_name="%(app_label)s_%(class)ss",
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Title of resource')
    )

    is_template = models.BooleanField(
        default=False,
        verbose_name=_('Is a template'),
        help_text=_('Is a template')
    )

    seen = models.BooleanField(
        default=False,
        verbose_name=_('Seen'),
        help_text=_('Seen'),
    )

    is_vault = models.BooleanField(
        default=False,
        verbose_name=_('Is in vault'),
        help_text=_('Is in vault')
    )

    objects = querysets.ResourceQuerySet.as_manager()

    class Meta:
        abstract = True
        unique_together = ['parent', 'title', 'owner', 'matter']
        # Answer to why there is no common constrains, from django docs
        # You must always specify a unique name for the constraint. As such,
        # you cannot normally specify a constraint on an abstract base class,
        # since the Meta.constraints option is inherited by subclasses, with
        # exactly the same values for the attributes (including name) each
        # time.Instead, specify the constraints option on subclasses directly,
        # providing a unique name for each constraint.

    def __str__(self):
        model_name = self._meta.verbose_name
        return f"{model_name}: '{self.title}'"

    @property
    def is_global_template(self) -> bool:
        """Check if resource is admin template resource."""
        return (
            self.is_template and self.owner_id is None
        )

    @property
    def is_root_global_template(self) -> bool:
        """Check if resource is root admin template resource."""
        return (
            self.is_global_template and self.parent_id is None
        )

    @property
    def is_personal_template(self) -> bool:
        """Check if resource is personal template resource."""
        return self.is_template and self.owner_id

    @property
    def is_root_personal_template(self) -> bool:
        """Check if resource is root personal template resource."""
        return (
            self.is_personal_template and self.parent_id is None
        )

    def clean_matter(self):
        """Check that we are not trying to create template in matter."""
        if not self.matter_id:
            return

        if self.is_template:
            raise ValidationError(
                f'Template {self.__class__.__name__.lower()} can not be '
                f'placed in matter'
            )

    def clean_parent(self):
        """Validate resource's parent.

        Validate that resource is not parent to itself.
        Validate that resource is not child of it's child.

        """
        if not self.parent_id or not self.parent.parent_id:
            return

        if self.id == self.parent_id:
            raise ValidationError("Resource can't be parent to itself")

        if isinstance(self, Folder) and self.pk in self.parent.path:
            raise ValidationError("Parent can't become child")

        # Template resources can't have matter.
        if not self.is_template:
            return

        if self.parent_id and self.parent.matter_id:
            raise ValidationError(
                f'Template {self.__class__.__name__.lower()} can not be '
                f'placed in matter'
            )

    def clean_title(self):
        """Validate that resource is unique by name in root folder.

        unique_together doesn't catch cases when parent is null.

        """
        owner_id = self.matter.attorney_id if self.matter_id else self.owner_id
        duplicate = self.__class__.objects.filter(
            title=self.title,
            parent_id=self.parent_id,
            matter_id=self.matter_id,
            owner_id=owner_id
        ).exclude(pk=self.pk)
        if duplicate.exists():
            raise ValidationError(
                f'You are trying to upload a duplicate '
                f'{self.__class__.__name__.lower()}. '
                'Please try again.'
            )


class Folder(Resource):
    """Model represents file folder.

    Attributes:
        owner (AppUser):
            if it's personal folder, when it user itself
            if it's matter related folder, when it matter's attorney`
        matter (Matter): relation to matter
        parent (Folder): Shows if folder is inside other folder
        title (str): Title of folder
        path (list[int]):
            Materialized path of folder hierarchy. Learn more:
            http://www.monkeyandcrow.com/blog/hierarchies_with_postgres/
        is_shared (bool):
            Is folder shared with the client of matter? if shared, folder
            is visible for both client and attorney, client have access to
            files just in this matter's folder.
            Shared folder has to be created on matter creation.

    """

    path = ArrayField(
        models.IntegerField(),
        default=list,
        verbose_name=_('Path'),
        help_text=_('Materialized path of folder hierarchy')
    )

    is_shared = models.BooleanField(
        default=False,
        verbose_name=_('Is shared'),
        help_text=_(
            'Is folder shared between attorney and client'
        )
    )

    shared_with = models.ManyToManyField(
        'users.AppUser',
        related_name='shared_folder',
        verbose_name=_('Shared with'),
        help_text=_('Users with which folder is shared')
    )

    objects = querysets.FolderQuerySet.as_manager()

    class Meta(Resource.Meta):
        abstract = False
        verbose_name = _('Folder')
        verbose_name_plural = _('Folders')
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'parent'],
                condition=models.Q(matter__isnull=True),
                name='unique private root folder'
            ),
            models.UniqueConstraint(
                fields=['title', 'matter'],
                condition=models.Q(parent__isnull=True),
                name='unique matter root folder'
            ),
            models.UniqueConstraint(
                fields=['title', 'owner'],
                condition=models.Q(parent__isnull=True, matter__isnull=True),
                name='unique root folder'
            ),
            models.UniqueConstraint(
                fields=['matter', 'is_shared'],
                condition=models.Q(is_shared=True, matter__isnull=False),
                name='unique shared folder for matter'
            ),
            models.UniqueConstraint(
                fields=['is_template'],
                condition=models.Q(
                    owner__isnull=True, parent__isnull=True, is_template=True
                ),
                name='unique root template folder'
            ),
            models.CheckConstraint(
                check=~models.Q(pk=models.F('parent')),
                name="parent can become parent to itself"
            ),
            models.CheckConstraint(
                check=(
                    models.Q(is_shared=True, matter__isnull=False) |
                    models.Q(is_shared=False)
                ),
                name="shared folder must have matter"
            ),
        ]

    @property
    def shared_with_users(self):
        """Users who shared with"""
        return [self.matter.client.user] if self.is_shared else []

    @property
    def type(self) -> str:
        """Return type"""
        return 'Folder'

    def clean_parent(self):
        """Check that parent folder is not shared folder."""
        super().clean_parent()
        if not self.parent_id:
            return

        if self.parent.is_shared and self.parent.matter_id:
            raise ValidationError(
                "Matter shared folder can't contain sub-folders"
            )

    def clean_is_shared(self):
        """Check that we don't create extra shared folder for matter.

        Also check that we are not trying to create shared template folder.

        """
        if not self.is_shared:
            return
        if self.is_template:
            raise ValidationError(
                'Shared folder can not be template folder'
            )
        if not self.matter_id:
            raise ValidationError(
                'Shared folder can be only created for matters'
            )
        if self.matter_id:
            duplicate = self.__class__.objects.filter(
                is_shared=True, matter_id=self.matter_id
            ).exclude(pk=self.pk)
            if duplicate.exists():
                raise ValidationError(
                    'There are can be only one shared folder per matter'
                )

    def update_path(self):
        """Update path field for self and children."""
        if not self.parent_id:
            self.path = [self.pk]
        else:
            self.path = self.parent.path + [self.pk]

    def save(self, **kwargs):
        """Update path field for folder and it's subfolders."""
        super().save(**kwargs)
        self.update_path()
        super().save()
        # TODO find a better solution to update subfolders paths
        for folder in self.folders.all():
            folder.save()


class Document(Resource):
    """Model represents document(file) in library.

    This models stores simple data about file stored in app, like title,
    link to s3, author and etc.

    Attributes:
`       owner (AppUser):
            if it's personal folder, when it user itself
            if it's matter related folder, when it matter's attorney`
        matter (Matter): relation to matter
        parent (Folder): Folder where document is stored
        created_by (AppUser): Link to the author of document
        mime_type (str): Mime type of file
        file (file): Document's file in s3 storage
        title (str): Title of document

    """

    created_by = models.ForeignKey(
        'users.AppUser',
        on_delete=models.PROTECT,
        verbose_name=_('Created by'),
        related_name='created_documents',
    )

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

    shared_with = models.ManyToManyField(
        'users.AppUser',
        related_name='file',
        verbose_name=_('Shared with'),
        help_text=_('Users with which document is shared')
    )

    transaction_id = models.CharField(
        blank=True,
        help_text='Transaction ID',
        max_length=128,
        null=True,
        verbose_name='Transaction ID'
    )

    objects = querysets.DocumentQuerySet.as_manager()

    class Meta(Resource.Meta):
        abstract = False
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'parent'],
                condition=models.Q(matter__isnull=True),
                name='unique private root document'
            ),
            models.UniqueConstraint(
                fields=['title', 'matter'],
                condition=models.Q(parent__isnull=True),
                name='unique matter root document'
            ),
            models.UniqueConstraint(
                fields=['title', 'owner'],
                condition=models.Q(parent__isnull=True, matter__isnull=True),
                name='unique root document'
            ),
        ]

    @property
    def is_shared_folder_document(self) -> bool:
        """Check if Document belongs to `shared_folder`."""
        if not self.parent_id:
            return False
        return self.parent.is_shared

    @property
    def type(self) -> str:
        """Return type"""
        return 'Document'

    def clean(self):
        """Check that file has mime type."""
        super().clean()
        mime_type = mimetypes.guess_type(str(self.file))[0]
        if not mime_type:
            raise ValidationError(
                "Failed to determine mime type of file. File probably doesn't "
                "have an extension."
            )

    @classmethod
    def client_documents(cls, client):
        """
        Extracts and return document queryset
        for client related documents
        """
        # client personal documents
        documents = cls.objects.filter(owner=client.user)

        # appending client matters related documents
        documents |= cls.objects.filter(matter__in=client.matters.all())

        return documents
