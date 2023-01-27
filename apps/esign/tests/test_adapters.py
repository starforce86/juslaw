from unittest.mock import MagicMock

from rest_framework.exceptions import APIException

import pytest
from docusign_esign import Document, EventNotification, Signer
from docusign_esign.client.api_exception import \
    ApiException as DocuSignAPIException

from libs.docusign import constants
from libs.docusign.exceptions import (
    CreateEditEnvelopeViewException,
    NoEnvelopeExistsException,
)

from apps.users import factories as users_factories
from apps.users.models import AppUser

from .. import adapters, factories, models
from ..exceptions import SaveUserConsentException


class TestHelpers:
    """Class with adapters `helpers` functions tests."""

    def test_get_envelope_documents_no_documents(
        self, envelope: models.Envelope
    ):
        """Test `get_envelope_documents` method when envelope has no documents.
        """
        assert adapters.get_envelope_documents(envelope) == []

    def test_get_envelope_documents_with_documents(
        self, envelope: models.Envelope
    ):
        """Test `get_envelope_documents` method when envelope has documents.
        """
        factories.ESignDocumentFactory(envelope=envelope)
        envelope_documents = adapters.get_envelope_documents(envelope)
        assert len(envelope_documents) == 1
        assert isinstance(envelope_documents[0], Document)

    def test_get_envelope_recipients(self, envelope: models.Envelope):
        """Test `get_envelope_recipients` method."""
        recipients = adapters.get_envelope_recipients(envelope)
        assert len(recipients) == 2
        assert isinstance(recipients[0], Signer)
        assert recipients[0].email == envelope.matter.attorney.email
        assert recipients[1].email == envelope.matter.client.email

    def test_get_envelope_notification(self, envelope: models.Envelope):
        """Test `get_envelope_notification` method."""
        envelope_notification = adapters.get_envelope_notification(
            'http://example.com'
        )
        assert isinstance(envelope_notification, EventNotification)

        # check that all `expected` envelope statuses are defined in result
        expected_statuses = [
            constants.ENVELOPE_STATUS_SENT,
            constants.ENVELOPE_STATUS_COMPLETED,
            constants.ENVELOPE_STATUS_DECLINED,
            constants.ENVELOPE_STATUS_VOIDED
        ]
        result_events = envelope_notification.envelope_events
        assert len(result_events) == len(expected_statuses)
        assert set(ev.envelope_event_status_code for ev in result_events) \
            == set(expected_statuses)


@pytest.fixture(scope="function")
def user_no_esign_profile(django_db_blocker) -> AppUser:
    """Create user without ESign profile."""
    with django_db_blocker.unblock():
        return users_factories.AppUserFactory()


@pytest.fixture(scope="function")
def user_with_esign_profile(
    django_db_blocker, esign_profile: models.ESignProfile
) -> AppUser:
    """Create user with ESign profile and `docusign_id` in it."""
    with django_db_blocker.unblock():
        return esign_profile.user


@pytest.fixture(scope="module")
def user_with_esign_profile_no_docusign_id(django_db_blocker) -> AppUser:
    """Create user with ESign profile, but no `docusign_id` in it."""
    with django_db_blocker.unblock():
        profile = factories.ESignProfileFactory(docusign_id=None)
        return profile.user


@pytest.fixture
def docusign_user(
    request,
    user_no_esign_profile: AppUser,
    user_with_esign_profile: AppUser,
    user_with_esign_profile_no_docusign_id: AppUser,
) -> AppUser:
    """Fixture to use fixtures in decorator parametrize for users."""
    mapping = {
        'user_no_esign_profile': user_no_esign_profile,
        'user_with_esign_profile': user_with_esign_profile,
        'user_with_esign_profile_no_docusign_id':
            user_with_esign_profile_no_docusign_id,
    }
    return mapping.get(request.param)


class TestDocuSignAdapter:
    """Class with tests related to `DocuSignAdapter`."""

    @pytest.mark.parametrize(
        argnames='docusign_user',
        argvalues=[
            None,
            'user_no_esign_profile',
            'user_with_esign_profile_no_docusign_id',
            'user_with_esign_profile'
        ],
        indirect=True
    )
    def test_init(
        self, docusign_user: str, mocker
    ):
        """Check that `__init__` method works correctly.

        Check that method is correctly called for different situations:

            1. No user is set.
            2. User is set, but has no esign profile.
            3. User is set, has esign profile, but no `docusign_id` is defined.
            4. User is set, has esign profile with defined `docusign_id`.

        """
        docusign_client_init = mocker.patch(
            'libs.docusign.clients.DocuSignClient.__init__',
        )
        docusign_client_init.return_value = None
        adapters.DocuSignAdapter(user=docusign_user)

        profile = getattr(docusign_user, 'esign_profile', None)
        docusign_id = getattr(profile, 'docusign_id') if profile else None
        docusign_client_init.assert_called_with(user_id=docusign_id)

    def test_is_consent_obtained(
        self, mocker, user_with_esign_profile: AppUser
    ):
        """Test `is_consent_obtained` method.

        Check that if user already obtained a consent  -> `True` value will be
        returned without extra manipulations with `esign profiles`.

        """
        is_consent_obtained_mock = mocker.patch(
            'libs.docusign.clients.DocuSignClient.is_consent_obtained',
        )
        is_consent_obtained_mock.return_value = True
        is_consent_obtained = adapters.DocuSignAdapter(
            user=user_with_esign_profile
        ).is_consent_obtained()

        assert is_consent_obtained
        assert user_with_esign_profile.esign_profile.docusign_id is not None

    def test_is_consent_obtained_no_consent(
        self, mocker, user_with_esign_profile: AppUser
    ):
        """Test `is_consent_obtained` method.

        Check that if user has no consent yet -> `False` value will be
        returned, all users esign profiles with the same `docusign_id` will be
        deleted and original user `docusign_id` will be refreshed.

        """
        is_consent_obtained_mock = mocker.patch(
            'libs.docusign.clients.DocuSignClient.is_consent_obtained',
        )
        is_consent_obtained_mock.return_value = False

        # user with the same `docusign_id`
        another_profile = factories.ESignProfileFactory(
            docusign_id=user_with_esign_profile.esign_profile.docusign_id
        )

        is_consent_obtained = adapters.DocuSignAdapter(
            user=user_with_esign_profile
        ).is_consent_obtained()

        assert is_consent_obtained is False
        assert user_with_esign_profile.esign_profile.docusign_id is None
        with pytest.raises(models.ESignProfile.DoesNotExist):
            another_profile.refresh_from_db()

    def test_get_consent_link_no_esign_profile(
        self, user_no_esign_profile: AppUser
    ):
        """Test `get_consent_link` method.

        Check that if user without esign profile tries to get consent link,
        there will be created a new `esign` profile for him with specified
        `return_url`.

        """
        with pytest.raises(models.ESignProfile.DoesNotExist):
            user_no_esign_profile.esign_profile

        docusign_client = adapters.DocuSignAdapter(user=user_no_esign_profile)

        return_url = 'http://example.com'
        consent_link = docusign_client.get_consent_link(return_url)
        esign_profile = user_no_esign_profile.esign_profile
        expected_consent_link = docusign_client.client \
            .get_consent_link(state=esign_profile.consent_id) \
            if esign_profile else None

        assert esign_profile is not None
        assert esign_profile.return_url == return_url
        assert consent_link == expected_consent_link

    def test_get_consent_link_with_esign_profile(
        self, user_with_esign_profile: AppUser
    ):
        """Test `get_consent_link` method.

        Check that if user with esign profile tries to get consent link,
        existing profile will be updated with specified `return_url`.

        """
        esign_profile = user_with_esign_profile.esign_profile
        assert esign_profile is not None

        docusign_client = adapters.DocuSignAdapter(
            user=user_with_esign_profile
        )

        return_url = 'http://example.com'
        consent_link = docusign_client.get_consent_link(return_url)
        expected_consent_link = docusign_client.client \
            .get_consent_link(state=esign_profile.consent_id) \
            if esign_profile else None

        esign_profile.refresh_from_db()
        assert esign_profile.return_url == return_url
        assert consent_link == expected_consent_link

    @pytest.mark.parametrize(
        argnames='docusign_user',
        argvalues=[
            'user_no_esign_profile',
            'user_with_esign_profile',
        ],
        indirect=True
    )
    def test_save_consent_bad_esign_profile(self, docusign_user: AppUser):
        """Test `save_consent` method.

        Check that exception will be raised in situations:

            - when user has no `esign_profile`
            - when user `esign_profile` state doesn't match adapter's one

        """
        with pytest.raises(SaveUserConsentException):
            adapters.DocuSignAdapter(
                user=docusign_user
            ).save_consent(code='test_code', state='test_state')

    def test_save_consent(
        self, user_with_esign_profile: AppUser,
        esign_profile: models.ESignProfile, mocker
    ):
        """Test `save_consent` method with valid esign profile

        Check that `docusign_id` will be correctly set to user's esign profile.

        """
        process_consent_mock = mocker.patch(
            'libs.docusign.clients.DocuSignClient.process_consent',
        )
        process_consent_mock.return_value = 'fake docusign_id'
        adapters.DocuSignAdapter(user=user_with_esign_profile).save_consent(
            code='test_code',
            state=str(esign_profile.consent_id)
        )
        esign_profile.refresh_from_db()
        assert esign_profile.docusign_id == 'fake docusign_id'

    @pytest.mark.parametrize(
        'type,is_open', [
            (models.Envelope.TYPE_INITIAL, True),
            (models.Envelope.TYPE_EXTRA, False)
        ]
    )
    def test_create_envelope_no_envelope(
        self, type: str, is_open: bool, matter: models.Matter,
        user_with_esign_profile: AppUser, mocker
    ):
        """Test `create_envelope` method.

        Check when no envelope exists in DB, there will be created new envelope
        in DB with correct `type`, `status` and in DocuSign.

        """
        create_envelope_mock = mocker.patch(
            'libs.docusign.clients.DocuSignClient.create_envelope',
        )
        create_envelope_mock.return_value = MagicMock(
            envelope_id='fake envelope docusign_id'
        )
        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        document_path = user_with_esign_profile.avatar.path
        envelope = adapters.DocuSignAdapter(user=user_with_esign_profile) \
            .create_envelope(
                type=type,
                matter=matter,
                is_open=is_open,
                documents=[document_path]
            )

        expected_status = constants.ENVELOPE_STATUS_CREATED if is_open \
            else constants.ENVELOPE_STATUS_SENT
        expected_matter_status = models.Matter.STATUS_OPEN if is_open \
            else envelope.matter.status

        assert envelope is not None
        assert envelope.documents.count() == 1
        assert envelope.type == type
        assert envelope.status == expected_status
        assert envelope.docusign_id == 'fake envelope docusign_id'
        assert matter.status == expected_matter_status

    @pytest.mark.parametrize('is_open', [True, False])
    def test_create_envelope(
        self, is_open: bool, matter: models.Matter, envelope: models.Envelope,
        user_with_esign_profile: AppUser, mocker
    ):
        """Test `create_envelope` method.

        Check when envelope exists in DB, there will be created new envelope
        in DocuSign only and matter status will be updated if it is needed.

        """
        create_envelope_mock = mocker.patch(
            'libs.docusign.clients.DocuSignClient.create_envelope',
        )
        create_envelope_mock.return_value = MagicMock(
            envelope_id='fake envelope docusign_id'
        )

        matter.status = models.Matter.STATUS_OPEN
        matter.save()

        result_envelope = adapters.DocuSignAdapter(
            user=user_with_esign_profile
        ).create_envelope(envelope=envelope, is_open=is_open)

        expected_status = constants.ENVELOPE_STATUS_CREATED if is_open \
            else constants.ENVELOPE_STATUS_SENT
        expected_matter_status = models.Matter.STATUS_OPEN if is_open \
            else envelope.matter.status
        envelope.refresh_from_db()

        assert result_envelope.id == envelope.id
        assert result_envelope.documents.count() == envelope.documents.count()
        assert result_envelope.type == envelope.type
        assert envelope.status == expected_status
        assert envelope.docusign_id == 'fake envelope docusign_id'
        assert matter.status == expected_matter_status

    def test_void_envelope_no_envelope(
        self, user_with_esign_profile: AppUser, mocker
    ):
        """Test `void_envelope` method.

        Check when no `envelope` is set in method -> no extra requests to
        DocuSign is made and no envelope deletion is performed.

        """
        update_envelope_mock = mocker.patch(
            'libs.docusign.clients.DocuSignClient.update_envelope',
        )
        delete_envelope_mock = mocker.patch(
            'apps.esign.models.Envelope.delete'
        )
        adapters.DocuSignAdapter(user=user_with_esign_profile).void_envelope(
            envelope=None,
            voided_reason=None
        )
        update_envelope_mock.assert_not_called()
        delete_envelope_mock.assert_not_called()

    @pytest.mark.parametrize('status,is_sent', [
        (constants.ENVELOPE_STATUS_SIGNED, False),
        (constants.ENVELOPE_STATUS_SENT, True),
        (constants.ENVELOPE_STATUS_DELIVERED, True),
    ])
    def test_void_envelope(
        self, status: str, is_sent: bool, user_with_esign_profile: AppUser,
        envelope: models.Envelope, mocker
    ):
        """Test `void_envelope` method.

        Check that correct actions are performed when Envelope is voided.

        """
        update_envelope_mock = mocker.patch(
            'libs.docusign.clients.DocuSignClient.update_envelope',
        )
        delete_envelope_mock = mocker.patch(
            'apps.esign.models.Envelope.delete'
        )

        envelope.status = status
        envelope.save()

        adapters.DocuSignAdapter(user=user_with_esign_profile).void_envelope(
            envelope=envelope,
            voided_reason='some reason'
        )

        # check that request to DocuSign was made
        if is_sent:
            update_envelope_mock.assert_called()
        else:
            update_envelope_mock.assert_not_called()

        delete_envelope_mock.assert_called()

    @pytest.mark.parametrize('docusign_id', [None, 'fake id'])
    def test_get_envelope_edit_link(
        self, docusign_id: str or None, user_with_esign_profile: AppUser,
        envelope: models.Envelope, mocker
    ):
        """Test `get_envelope_edit_link` method."""
        get_envelope_edit_link_mock = mocker.patch(
            'libs.docusign.clients.DocuSignClient.get_envelope_edit_link',
        )
        get_envelope_edit_link_mock.return_value = 'fake link'

        envelope.docusign_id = docusign_id
        edit_link = adapters.DocuSignAdapter(user=user_with_esign_profile) \
            .get_envelope_edit_link(envelope=envelope)

        assert edit_link == '' if not docusign_id else 'fake link'

    @pytest.mark.parametrize('error_code, exception', [
        ('ENVELOPE_DOES_NOT_EXIST', NoEnvelopeExistsException),
        ('FAKE_EXCEPTION', CreateEditEnvelopeViewException)
    ])
    def test_get_envelope_edit_link_exceptions(
        self, error_code: str, exception: APIException,
        user_with_esign_profile: AppUser, envelope: models.Envelope, mocker
    ):
        """Test `get_envelope_edit_link` method exceptions.

        Check that correct exception is raised depending on a `error_code`.

        """
        mocker.patch(
            'libs.docusign.clients.DocuSignClient.is_consent_obtained',
            return_value=True
        )
        mocker.patch(
            'libs.docusign.clients.DocuSignClient.update_token',
            return_value=None
        )
        mocker.patch(
            'docusign_esign.apis.envelopes_api.EnvelopesApi.__init__',
            side_effect=DocuSignAPIException(
                http_resp=MagicMock(data={'errorCode': error_code})
            )
        )

        with pytest.raises(exception):
            adapters.DocuSignAdapter(user=user_with_esign_profile) \
                .get_envelope_edit_link(envelope=envelope)
