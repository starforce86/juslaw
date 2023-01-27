from ....business.models import Matter
from ....business.services import get_matter_shared_folder
from ....documents.factories import DocumentFactory
from ....users.models import Attorney, Client
from ...services import resources


class TestDocumentSharedNotificationResource:
    """Test `DocumentSharedNotificationResource`."""

    def test_get_recipients(
        self,
        client: Client,
        attorney: Attorney,
        matter: Matter,
    ):
        """Test get_recipients method."""
        instance = DocumentFactory(
            created_by=attorney.user,
            matter=matter,
            parent=get_matter_shared_folder(matter=matter)
        )
        resource = resources.DocumentSharedNotificationResource(
            instance=instance
        )
        assert client.user in resource.get_recipients()
