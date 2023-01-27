from django.db.models import Model

from apps.documents.models import Document

from ...models import Matter


def is_created(instance: Model, created: bool = None, **kwargs) -> bool:
    """Check if instance is created."""
    # use `created` from signal if it was set
    if created is not None:
        return created
    return instance._state.adding


def is_not_created(instance: Model, created: bool = None, **kwargs) -> bool:
    """Check if instance is not created."""
    return not is_created(instance, created, **kwargs)


def is_shared_folder_document(instance: Document, **kwargs) -> bool:
    """Check if document instance is related to a matter shared folder."""
    return instance.is_shared_folder_document


def is_not_open(instance: Matter, **kwargs) -> bool:
    """Check if matter instance is not draft."""
    return not instance.is_open
