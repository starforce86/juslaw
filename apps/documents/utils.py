from apps.users.models import AppUser

from .models import Document, Folder, Resource


def is_resource_available_for_user(resource: Resource, user: AppUser) -> bool:
    """Check if resource is available for user."""
    if resource.owner_id == user.pk:
        return True
    if user.is_attorney:
        return resource.matter.attorney.pk == user.pk
    return resource.matter.client.pk == user.pk


def copy_folder_resources(folder: Folder, subfolders, documents):
    """Copy folders and documents to a new folder.

    TODO: Needs improvements
        Problem: folders on each level are copied one by one. And on every step
        they do query to get subfolder and documents. It potentially can lead
        to performance issues.

    """
    for subfolder in subfolders:
        sub_subfolders = subfolder.folders.all()
        sub_documents = subfolder.documents.all()
        subfolder = create_folder_copy(subfolder, folder)
        subfolder.save()
        copy_folder_resources(subfolder, sub_subfolders, sub_documents)

    Document.objects.bulk_create(
        create_document_copy(document, folder)
        for document in documents
    )


def create_folder_copy(folder: Folder, parent: Folder) -> Folder:
    """Create folder copy."""
    folder.pk = None
    folder.parent = parent
    return folder


def create_document_copy(document: Document, folder: Folder) -> Document:
    """Create document copy."""
    document.pk = None
    document.parent = folder
    return document
