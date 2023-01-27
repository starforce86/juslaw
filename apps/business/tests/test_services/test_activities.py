from unittest.mock import MagicMock

import arrow
import pytest

from apps.business.activities_rules import MatterStatusActivityRule
from apps.business.services.invoices import send_invoice_to_recipients
from apps.documents import factories as docs_factories

from ... import factories
from ...models import Matter
from ...services import get_matter_shared_folder


def create_activity_mock(mocker: MagicMock):
    """Shortcut to prepare a `create_activity` mock."""
    return mocker.patch(
        'apps.business.models.Activity.objects.create'
    )


class TestMatterCreatedActivityRule:
    """Tests `Matter created` Activity Rule."""

    def test_matter_created(self, mocker):
        """Check when new matter is created -> there appeared a new `activity`.

        When new matter is created only one `created` activity should appear.

        """
        create_activity = create_activity_mock(mocker)
        matter = factories.MatterFactory()
        create_activity.assert_called_once_with(
            matter=matter,
            title=f'Matter created by {matter.attorney.user.full_name}'
        )

    def test_matter_updated(self, activities_matter: Matter, mocker):
        """Check when matter is updated -> no new `activities` should appear.
        """
        create_activity = create_activity_mock(mocker)
        activities_matter.save()
        create_activity.assert_not_called()


class TestMatterStatusChangedActivityRules:
    """Tests `Matter status changed` Activity Rule."""

    @pytest.mark.parametrize(
        'status_from,transition,params', [
            (Matter.STATUS_OPEN, 'open', {}),
            (Matter.STATUS_CLOSE, 'close', {
                'completed': arrow.now().datetime
            })
        ]
    )
    def test_matter_status_update(
        self, activities_matter: Matter, status_from: str, transition: str,
        params: dict, mocker
    ):
        """Check when matter is updated -> new `activity` appears."""
        activities_matter.status = status_from
        activities_matter.save()
        create_activity = create_activity_mock(mocker)

        # add client `user` as extra transition parameter to check non-default
        # behavior of MatterStatusActivityRule
        extra_params = params.copy()
        extra_params['user'] = activities_matter.client.user

        getattr(activities_matter, transition)(**extra_params)
        create_activity.assert_called_once_with(
            matter=activities_matter,
            title=MatterStatusActivityRule(None, None).get_activity_msg(
                activities_matter, method_kwargs={
                    'user': activities_matter.client.user
                }
            )
        )

    @pytest.mark.parametrize(
        'transition', ('pending', 'activate', 'make_draft')
    )
    def test_matter_reopened(
        self, activities_matter: Matter, transition: str, mocker
    ):
        """Check when revoked matter reopened again.

        Check that separate message is created, when matter is reopened after
        `revoked`.

        """
        activities_matter.status = Matter.STATUS_REVOKED
        activities_matter.save()
        create_activity = create_activity_mock(mocker)
        getattr(activities_matter, transition)(
            user=activities_matter.client.user
        )
        create_activity.assert_called_once_with(
            matter=activities_matter,
            title=f'Matter reopened by '
                  f'{activities_matter.client.user.full_name}'
        )


class TestInvoiceSentActivityRule:
    """Tests `Invoice is sent` Activity Rule."""

    def test_invoice_is_created(self, activities_matter: Matter, mocker):
        """Check when invoice is created -> no new `activity` appears."""
        create_activity = create_activity_mock(mocker)
        factories.InvoiceFactory(matter=activities_matter)
        create_activity.assert_not_called()

    def test_invoice_is_sent(self, activities_matter: Matter, mocker):
        """Check when invoice is sent -> new `activity` appears."""
        create_activity = create_activity_mock(mocker)
        send_email = mocker.patch(
            'libs.notifications.email.EmailNotification.send'
        )
        send_email.return_value = True

        invoice = factories.InvoiceFactory(matter=activities_matter)
        send_invoice_to_recipients(
            invoice=invoice,
            recipient_list=[],
            user=activities_matter.client.user
        )
        create_activity.assert_called_once_with(
            matter=activities_matter,
            title=f'Invoice was sent to client by '
                  f'{activities_matter.client.user.full_name}'
        )


class TestNoteAddedActivityRule:
    """Tests `Note added` Activity Rule."""

    def test_note_is_created(self, activities_matter: Matter, mocker):
        """Check when note is created -> new `activity` appears."""
        create_activity = create_activity_mock(mocker)
        note = factories.NoteFactory(matter=activities_matter)
        create_activity.assert_called_once_with(
            matter=activities_matter,
            title=f'Note has been added by {note.created_by.full_name}'
        )

    def test_note_is_updated(self, activities_matter: Matter, mocker):
        """Check when note is updated -> no new `activity` appears."""
        note = factories.NoteFactory(matter=activities_matter)
        create_activity = create_activity_mock(mocker)
        note.save()
        create_activity.assert_not_called()


class TestMessageAddedActivityRule:
    """Tests `Message added` Activity Rule."""

    def test_message_is_created(self, activities_matter: Matter, mocker):
        """Check when message is created -> new `activity` appears."""
        create_activity = create_activity_mock(mocker)
        post = factories.MatterPostFactory(topic__matter=activities_matter)
        create_activity.assert_called_once_with(
            matter=activities_matter,
            title=f'Message has been added by {post.author.full_name}'
        )

    def test_message_is_updated(self, activities_matter: Matter, mocker):
        """Check when message is updated -> no new `activity` appears."""
        post = factories.MatterPostFactory(topic__matter=activities_matter)
        create_activity = create_activity_mock(mocker)
        post.save()
        create_activity.assert_not_called()


class TestNewFileInSharedFolderActivityRule:
    """Tests `New file in a shared folder` Activity Rule."""

    def test_shared_document_created(self, activities_matter: Matter, mocker):
        """Check when shared document is created -> new `activity` appears."""
        create_activity = create_activity_mock(mocker)
        doc = docs_factories.DocumentFactory(
            parent=get_matter_shared_folder(activities_matter),
        )
        create_activity.assert_called_once_with(
            matter=activities_matter,
            title=f'New file has been uploaded to shared folder by '
                  f'{doc.created_by.full_name}'
        )

    def test_shared_document_updated(self, activities_matter: Matter, mocker):
        """Check when shared document is updated -> no new `activity` appears.
        """
        doc = docs_factories.DocumentFactory(
            parent=get_matter_shared_folder(activities_matter),
        )
        create_activity = create_activity_mock(mocker)
        doc.save()
        create_activity.assert_not_called()

    def test_not_shared_document_created(
        self, activities_matter: Matter, mocker
    ):
        """Check when not shared document is created -> new `activity` appears.
        """
        create_activity = create_activity_mock(mocker)
        docs_factories.DocumentFactory()
        create_activity.assert_not_called()
