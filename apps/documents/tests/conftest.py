from typing import Dict, Union

import pytest

from apps.business.factories import MatterSharedWithFactory

from ...business.models import Matter
from ...business.services import get_matter_shared_folder
from ...users import models as user_models
from .. import factories, models


@pytest.fixture(scope='session')
def private_attorney_folder(
    django_db_blocker, attorney: user_models.Attorney
) -> models.Folder:
    """Create private folder for attorney."""
    with django_db_blocker.unblock():
        return factories.FolderFactory(owner=attorney.user)


@pytest.fixture(scope='session')
def private_shared_attorney_folder(
    django_db_blocker, shared_attorney: user_models.Attorney
) -> models.Folder:
    """Create private folder for shared attorney."""
    with django_db_blocker.unblock():
        return factories.FolderFactory(owner=shared_attorney.user)


@pytest.fixture(scope='session')
def private_support_folder(
    django_db_blocker, support: user_models.Support
) -> models.Folder:
    """Create private folder for support."""
    with django_db_blocker.unblock():
        return factories.FolderFactory(owner=support.user)


@pytest.fixture(scope='session')
def matter_folder(django_db_blocker, matter: Matter) -> models.Folder:
    """Create matter folder."""
    with django_db_blocker.unblock():
        return factories.FolderFactory(matter=matter)


@pytest.fixture(scope='session')
def shared_folder(django_db_blocker, matter: Matter) -> models.Folder:
    """Get shared folder from test matter."""
    with django_db_blocker.unblock():
        return get_matter_shared_folder(matter)


@pytest.fixture(scope='session')
def other_matter_folder(
    django_db_blocker, another_matter: Matter
) -> models.Folder:
    """Create another matter folder."""
    with django_db_blocker.unblock():
        return factories.MatterFolderFactory(matter=another_matter)


@pytest.fixture(scope='session')
def other_shared_folder(
    django_db_blocker, another_matter: Matter
) -> models.Folder:
    """Get shared folder from another matter."""
    with django_db_blocker.unblock():
        return get_matter_shared_folder(another_matter)


@pytest.fixture(scope='session', autouse=True)
def root_admin_template_folder(django_db_blocker) -> models.Folder:
    """Generate template folder and it's documents.

    If we run tests again with reuse-db and with use of transactional db
    fixture, we won't have global templates, because migration file creates
    them and won't run with reuse-db and pytest cleans db after each test run.
    So on next run we won't have global templates.

    """
    with django_db_blocker.unblock():
        models.Folder.objects.filter(is_template=True, owner=None).delete()
        global_folder = factories.FolderFactory(
            is_template=True,
            title='Template Folder',
            parent=None,
            owner=None,
            matter=None,
        )
        return global_folder


@pytest.fixture(scope='session', autouse=True)
def admin_template_folder(
    django_db_blocker, root_admin_template_folder: models.Folder
) -> models.Folder:
    """Get not root admin template folder."""
    with django_db_blocker.unblock():
        return factories.FolderFactory(
            is_template=True, parent=root_admin_template_folder
        )


@pytest.fixture(scope='session')
def root_attorney_template_folder(
    django_db_blocker, attorney: user_models.Attorney
) -> models.Folder:
    """Get root template folder from attorney."""
    with django_db_blocker.unblock():
        return attorney.user.folders.get(
            is_template=True, parent=None, matter=None
        )


@pytest.fixture(scope='session')
def attorney_template_folder(
    django_db_blocker, root_attorney_template_folder
) -> models.Folder:
    """Create template folder from attorney."""
    with django_db_blocker.unblock():
        return factories.FolderFactory(
            is_template=True, parent=root_attorney_template_folder
        )


@pytest.fixture(scope='session')
def root_shared_attorney_template_folder(
    django_db_blocker, shared_attorney: user_models.Attorney
) -> models.Folder:
    """Get root template folder from attorney."""
    with django_db_blocker.unblock():
        return shared_attorney.user.folders.get(
            is_template=True, parent=None, matter=None
        )


@pytest.fixture(scope='session')
def shared_attorney_template_folder(
    django_db_blocker, root_shared_attorney_template_folder
) -> models.Folder:
    """Create template folder from attorney."""
    with django_db_blocker.unblock():
        return factories.FolderFactory(
            is_template=True, parent=root_shared_attorney_template_folder
        )


@pytest.fixture(scope='session')
def root_support_template_folder(
    django_db_blocker, support: user_models.Support
) -> models.Folder:
    """Get root template folder from support."""
    with django_db_blocker.unblock():
        return support.user.folders.get(
            is_template=True, parent=None, matter=None
        )


@pytest.fixture(scope='session')
def support_template_folder(
    django_db_blocker, root_support_template_folder
) -> models.Folder:
    """Create template folder from support."""
    with django_db_blocker.unblock():
        return factories.FolderFactory(
            is_template=True, parent=root_support_template_folder
        )


@pytest.fixture(scope='session')
def shared_matter_folder(django_db_blocker, matter: Matter) -> models.Folder:
    """Create shared matter folder for testing."""
    with django_db_blocker.unblock():
        shared = MatterSharedWithFactory(user=matter.attorney.user)
        return factories.FolderFactory(matter=shared.matter)


@pytest.fixture
def folder_mapping(
    private_attorney_folder: models.Folder,
    private_shared_attorney_folder: models.Folder,
    private_support_folder: models.Folder,
    matter_folder: models.Folder,
    other_matter_folder: models.Folder,
    shared_folder: models.Folder,
    other_shared_folder: models.Folder,
    root_admin_template_folder: models.Folder,
    admin_template_folder: models.Folder,
    root_attorney_template_folder: models.Folder,
    attorney_template_folder: models.Folder,
    root_shared_attorney_template_folder: models.Folder,
    shared_attorney_template_folder: models.Folder,
    root_support_template_folder: models.Folder,
    support_template_folder: models.Folder,
    shared_matter_folder: models.Folder,
) -> Dict[str, models.Folder]:
    """Get fixture folder mapping."""
    mapping = dict(
        private_attorney_folder=private_attorney_folder,
        private_shared_attorney_folder=private_shared_attorney_folder,
        private_support_folder=private_support_folder,
        matter_folder=matter_folder,
        other_matter_folder=other_matter_folder,
        shared_folder=shared_folder,
        other_shared_folder=other_shared_folder,
        root_admin_template_folder=root_admin_template_folder,
        admin_template_folder=admin_template_folder,
        root_attorney_template_folder=root_attorney_template_folder,
        attorney_template_folder=attorney_template_folder,
        root_shared_attorney_template_folder=root_shared_attorney_template_folder,  # noqa
        shared_attorney_template_folder=shared_attorney_template_folder,
        root_support_template_folder=root_support_template_folder,
        support_template_folder=support_template_folder,
        shared_matter_folder=shared_matter_folder,
    )
    return mapping


@pytest.fixture(scope='session')
def private_attorney_document(
    django_db_blocker, attorney: user_models.Attorney
) -> models.Document:
    """Create private document for testing."""
    with django_db_blocker.unblock():
        return factories.DocumentFactory(owner=attorney.user, parent=None)


@pytest.fixture(scope='session')
def private_shared_attorney_document(
    django_db_blocker, shared_attorney: user_models.Attorney
) -> models.Document:
    """Create private document for testing."""
    with django_db_blocker.unblock():
        return factories.DocumentFactory(
            owner=shared_attorney.user, parent=None
        )


@pytest.fixture(scope='session')
def private_support_document(
    django_db_blocker, support: user_models.Support
) -> models.Document:
    """Create private document for testing."""
    with django_db_blocker.unblock():
        return factories.DocumentFactory(owner=support.user, parent=None)


@pytest.fixture(scope='session')
def matter_document(django_db_blocker, matter: Matter) -> models.Document:
    """Create matter document for testing."""
    with django_db_blocker.unblock():
        return factories.DocumentFactory(matter=matter, parent=None)


@pytest.fixture(scope='session')
def shared_document(
    django_db_blocker, shared_folder: models.Folder
) -> models.Document:
    """Create shared document from test matter."""
    with django_db_blocker.unblock():
        return factories.DocumentFactory(parent=shared_folder)


@pytest.fixture(scope='session')
def other_matter_document(
    django_db_blocker, another_matter: Matter
) -> models.Document:
    """Create matter document for testing."""
    with django_db_blocker.unblock():
        return factories.DocumentFactory(matter=another_matter, parent=None)


@pytest.fixture(scope='session')
def other_shared_document(
    django_db_blocker, other_shared_folder: models.Folder
) -> models.Document:
    """Create shared document from test matter."""
    with django_db_blocker.unblock():
        return factories.DocumentFactory(parent=other_shared_folder)


@pytest.fixture(scope='session')
def admin_template_document(
    django_db_blocker, admin_template_folder
) -> models.Document:
    """Get admin template document."""
    with django_db_blocker.unblock():
        return admin_template_folder.documents.first()


@pytest.fixture(scope='session')
def attorney_template_document(
    django_db_blocker, attorney_template_folder: models.Folder
) -> models.Document:
    """Create template document for attorney."""
    with django_db_blocker.unblock():
        return attorney_template_folder.documents.first()


@pytest.fixture(scope='session')
def shared_attorney_template_document(
    django_db_blocker, shared_attorney_template_folder: models.Folder
) -> models.Document:
    """Create template document for shared attorney."""
    with django_db_blocker.unblock():
        return shared_attorney_template_folder.documents.first()


@pytest.fixture(scope='session')
def support_template_document(
    django_db_blocker, support_template_folder: models.Folder
) -> models.Document:
    """Create template document for support."""
    with django_db_blocker.unblock():
        return support_template_folder.documents.first()


@pytest.fixture(scope='session')
def shared_matter_document(
    django_db_blocker, shared_matter_folder: models.Folder
) -> models.Document:
    """Create shared document from test matter."""
    with django_db_blocker.unblock():
        return factories.DocumentFactory(parent=shared_matter_folder)


@pytest.fixture
def document_mapping(
    private_attorney_document: models.Document,
    private_shared_attorney_document: models.Document,
    private_support_document: models.Document,
    matter_document: models.Document,
    shared_document: models.Document,
    other_matter_document: models.Document,
    other_shared_document: models.Document,
    admin_template_document: models.Document,
    attorney_template_document: models.Document,
    shared_attorney_template_document: models.Document,
    support_template_document: models.Document,
    shared_matter_document: models.Document,
) -> Dict[str, models.Document]:
    """Get fixture document mapping."""
    mapping = dict(
        private_attorney_document=private_attorney_document,
        private_shared_attorney_document=private_shared_attorney_document,
        private_support_document=private_support_document,
        matter_document=matter_document,
        shared_document=shared_document,
        other_matter_document=other_matter_document,
        other_shared_document=other_shared_document,
        admin_template_document=admin_template_document,
        attorney_template_document=attorney_template_document,
        shared_attorney_template_document=shared_attorney_template_document,
        support_template_document=support_template_document,
        shared_matter_document=shared_matter_document,
    )
    return mapping


@pytest.fixture
def resource_mapping(
    folder_mapping: Dict[str, models.Folder],
    document_mapping: Dict[str, models.Document],
) -> Dict[str, Union[models.Folder, models.Document]]:
    """Get fixture resource mapping."""
    resource_mapping = {}
    resource_mapping.update(**folder_mapping)
    resource_mapping.update(**document_mapping)
    folder_mapping.update(**folder_mapping)
    return resource_mapping


@pytest.fixture
def folder(
    request, resource_mapping: Dict[str, Union[models.Folder, models.Document]]
) -> models.Folder:
    """Fixture to use folder fixtures in decorator parametrize."""
    return resource_mapping[request.param]


@pytest.fixture
def document(
    request, resource_mapping: Dict[str, Union[models.Folder, models.Document]]
) -> models.Document:
    """Fixture to use document fixtures in decorator parametrize."""
    return resource_mapping[request.param]
