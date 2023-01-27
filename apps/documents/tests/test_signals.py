from unittest.mock import MagicMock, patch

import pytest

from ...business.models import Matter
from ...business.services import get_matter_shared_folder
from ...users.models import Attorney
from .. import factories, models
from ..factories import DocumentFactory


@patch('apps.documents.signals.document_shared_by_attorney')
def test_document_shared_by_attorney_signal(
    signal_mock: MagicMock,
    matter: Matter,
    attorney: Attorney,
):
    """Test that `document_shared_by_attorney` signal works."""
    instance = DocumentFactory(
        created_by_id=attorney.pk,
        matter=matter,
        parent=get_matter_shared_folder(matter=matter)
    )
    signal_mock.send.assert_called_with(
        sender=instance.__class__, instance=instance
    )


@pytest.mark.parametrize(
    argnames='attr_to_check, folder, model_factory',
    argvalues=((
        ('is_template', 'attorney_template_folder', factories.FolderFactory),
        ('matter_id', 'matter_folder', factories.FolderFactory),
        ('owner_id', 'private_attorney_folder', factories.FolderFactory),
        ('is_template', 'attorney_template_folder', factories.DocumentFactory),
        ('matter_id', 'matter_folder', factories.DocumentFactory),
        ('owner_id', 'private_attorney_folder', factories.DocumentFactory),
    )),
    indirect=True
)
def test_signal_setters(
    attr_to_check: str, folder: models.Folder, model_factory
):
    """Test that resource inherits owner, matter and is_template for parent.

    Test that `set_is_template_for_resource` signal works.
    Test that `set_matter_for_resource` signal works.
    Test that `set_owner_for_resource` signal works.
    Test that `set_is_shared_for_resource` signal works.

    """
    resource = model_factory(parent=folder)
    assert getattr(folder, attr_to_check) == getattr(resource, attr_to_check)
