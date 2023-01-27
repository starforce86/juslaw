from ...users import models as user_models


def get_attorney_statistics(attorney: user_models.Attorney) -> dict:
    """Get attorney statistics for documents app."""
    documents_count = attorney.user.documents.count()

    return {
        'documents_count': documents_count,
    }
