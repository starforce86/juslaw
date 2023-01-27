from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

import pytest

from ...business.factories import MatterFactory
from ...business.models import Matter
from ...business.services import get_matter_shared_folder
from ...documents import factories, models
from ...users.factories import AttorneyFactory
from ...users.models import Attorney


class TestFolderModel:
    """Tests for `Folder` model."""

    def test_unique_shared_folder_on_matter_creation(self, matter):
        """Check that shared folder is created for matter."""
        assert models.Folder.objects.filter(
            matter=matter, is_shared=True
        ).exists()

        # Check that we can't create another shared folder for matter
        with pytest.raises(IntegrityError):
            factories.FolderFactory(matter=matter, is_shared=True)

    def test_parent_restriction_parent_to_itself(self, attorney: Attorney):
        """Check restrictions that resource can't be parent to itself."""
        folder = factories.FolderFactory(owner_id=attorney.pk)
        folder.parent = folder
        with pytest.raises(ValidationError):
            folder.clean()

        with pytest.raises(IntegrityError):
            folder.save()

    def test_parent_restriction_parent_to_its_child(self, attorney: Attorney):
        """Check restrictions that resource can't be child of it's child."""
        folder = factories.FolderFactory(owner_id=attorney.pk)
        child_folder = factories.FolderFactory(parent=folder)

        folder.parent = child_folder
        with pytest.raises(ValidationError):
            folder.clean()

    def test_folder_title_restriction_with_null_parent_or_matter(
        self, attorney: Attorney
    ):
        """Check restrictions that name of folder must be unique for owner.

        We test special case when parent is null or matter is null,
        unique_together doesn't catch these cases, and it breaks api.

        """
        owner_id = attorney.pk
        folder: models.Folder = factories.FolderFactory(owner_id=owner_id)
        other_folder: models.Folder = factories.FolderFactory(
            owner_id=owner_id
        )
        other_folder.title = folder.title

        with pytest.raises(ValidationError):
            other_folder.clean()

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                other_folder.save()

        # check that other user can save with same title
        other_folder.owner_id = AttorneyFactory().pk
        other_folder.clean()
        other_folder.save()

    def test_folder_title_restriction_with_null_parent(
        self, attorney: Attorney, matter: Matter
    ):
        """Check restrictions that name of folder must be unique for owner.

        We test special case when parent is null, unique_together doesn't catch
        these cases, and it breaks api.

        """
        owner_id = attorney.pk
        folder: models.Folder = factories.FolderFactory(
            matter=matter, owner_id=owner_id
        )
        other_folder: models.Folder = factories.FolderFactory(
            matter=matter, owner_id=owner_id
        )
        other_folder.title = folder.title

        with pytest.raises(ValidationError):
            other_folder.clean()

        with pytest.raises(IntegrityError):
            other_folder.save()

    def test_folder_title_restriction_with_null_matter(
        self, attorney: Attorney
    ):
        """Check restrictions that name of folder must be unique for owner.

        We test special case when matter is null, unique_together doesn't catch
        these cases, and it breaks api.

        """
        owner_id = attorney.pk
        parent = factories.FolderFactory(owner_id=owner_id)
        folder: models.Folder = factories.FolderFactory(
            parent=parent, owner_id=owner_id
        )
        other_folder: models.Folder = factories.FolderFactory(
            parent=parent, owner_id=owner_id
        )
        other_folder.title = folder.title

        with pytest.raises(ValidationError):
            other_folder.clean()

        with pytest.raises(IntegrityError):
            other_folder.save()

    def test_create_subfolder_for_shared_folder(self, attorney: Attorney):
        """Check we can't create subfolders for shared folder."""
        matter: Matter = MatterFactory(attorney=attorney)
        shared_folder: models.Folder = get_matter_shared_folder(matter)

        sub_folder = factories.FolderFactory(
            owner_id=attorney.pk, matter=matter
        )
        sub_folder.parent = shared_folder

        with pytest.raises(ValidationError):
            sub_folder.clean()

    def test_create_template_folder_in_matter(self, attorney: Attorney):
        """Check that we can't create template folder in matter."""
        matter: Matter = MatterFactory(attorney=attorney)
        folder = factories.FolderFactory(
            owner_id=attorney.pk, matter=matter
        )
        folder.is_template = True

        with pytest.raises(ValidationError):
            folder.clean()

    def test_create_second_root_admin_template_folder(self):
        """Check that we can't create second root admin template folder."""
        folder = factories.FolderFactory(owner=None, parent=None)
        folder.is_template = True

        with pytest.raises(ValidationError):
            folder.clean()

        with pytest.raises(IntegrityError):
            folder.save()

    def test_attorney_create_second_root_template_folder(
        self, attorney: Attorney
    ):
        """Check that attorney can't create second root template folder."""
        folder = factories.FolderFactory(owner_id=attorney.pk, parent=None)
        folder.is_template = True

        with pytest.raises(ValidationError):
            folder.clean()

        with pytest.raises(IntegrityError):
            folder.save()


class TestDocumentModel:
    """Tests for `Document` model."""

    def test_document_title_restriction_with_null_parent_or_matter(
        self, attorney: Attorney,
    ):
        """Check restrictions that name of document must be unique for owner.

        We test special case when parent is null or matter is null,
        unique_together doesn't catch these cases, and it breaks api.

        """
        owner_id = attorney.pk
        document: models.Document = factories.DocumentFactory(
            owner_id=owner_id, parent=None
        )
        other_document: models.Document = factories.DocumentFactory(
            owner_id=owner_id, parent=None
        )
        other_document.title = document.title

        with pytest.raises(ValidationError):
            other_document.clean()

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                other_document.save()

        # check that other user can save with same title
        other_document.owner_id = AttorneyFactory().pk
        other_document.clean()
        other_document.save()

    def test_document_title_restriction_with_null_parent(
        self, matter: Matter, attorney: Attorney
    ):
        """Check restrictions that name of document must be unique for owner.

        We test special case when parent is null, unique_together doesn't catch
        these cases, and it breaks api.

        """
        created_by_id = attorney.pk
        document: models.Document = factories.DocumentFactory(
            matter=matter, parent=None, created_by_id=created_by_id
        )
        other_document: models.Document = factories.DocumentFactory(
            matter=matter, parent=None, created_by_id=created_by_id
        )
        other_document.title = document.title

        with pytest.raises(ValidationError):
            other_document.clean()

        with pytest.raises(IntegrityError):
            other_document.save()

    def test_document_title_restriction_with_null_matter(
        self, attorney: Attorney
    ):
        """Check restrictions that name of document must be unique for owner.

        We test special case when matter is null, unique_together doesn't catch
        these cases, and it breaks api.

        """
        owner_id = attorney.pk
        parent = factories.FolderFactory(owner_id=owner_id)
        document: models.Document = factories.DocumentFactory(
            parent=parent, owner_id=owner_id, created_by_id=owner_id
        )
        other_document: models.Document = factories.DocumentFactory(
            parent=parent, owner_id=owner_id, created_by_id=owner_id
        )
        other_document.title = document.title

        with pytest.raises(ValidationError):
            other_document.clean()

        with pytest.raises(IntegrityError):
            other_document.save()

    def test_create_template_document_in_matter(self, attorney: Attorney):
        """Check that we can't create template document in matter."""
        matter: Matter = MatterFactory(attorney=attorney)
        document = factories.DocumentFactory(owner_id=attorney.pk,)
        document.is_template = True
        document.matter = matter

        with pytest.raises(ValidationError):
            document.clean()
