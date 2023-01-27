import pytest

from libs.docusign import constants, exceptions

from apps.business.models import Matter

from .. import factories, models, services


def test_get_matter_initial_envelope(
    envelope: models.Envelope, another_envelope: models.Envelope
):
    """Check `get_matter_initial_envelope` service method.

    Only `initial` matter envelopes should be returned.

    """
    matter = envelope.matter
    factories.EnvelopeFactory(matter=matter, type=models.Envelope.TYPE_EXTRA)
    result = services.get_matter_initial_envelope(matter)
    assert result == envelope


def test_get_matter_initial_envelope_no_envelopes(another_matter: Matter):
    """Test `get_matter_initial_envelope` method when matter has no envelopes.

    Check when matter has no envelopes - nothing would be returned.

    """
    assert services.get_matter_initial_envelope(another_matter) is None


def test_get_matter_transition_name_by_envelope_no_initial_envelope(
    another_matter: Matter
):
    """Test `get_matter_transition_name_by_envelope` service method.

    Check when matter has no `initial` envelope -> original
    `transition_name` would be returned without any mapping transformations.

    """
    result = services.get_matter_transition_name_by_envelope(
        another_matter, 'test'
    )
    assert result == 'test'


@pytest.mark.parametrize(
    'envelope_status,result_transition', [
        (constants.ENVELOPE_STATUS_CREATED, 'make_draft'),
        (constants.ENVELOPE_STATUS_COMPLETED, 'activate'),
        (constants.ENVELOPE_STATUS_DELIVERED, 'pending'),
    ]
)
def test_get_matter_transition_name_by_envelope(
    envelope: models.Envelope, envelope_status: str, result_transition: str
):
    """Test `get_matter_transition_name_by_envelope` service method.

    Check when `get_matter_transition_name_by_envelope` method is called,
    it changes original transition name to another one according to envelope
    status.

    """
    envelope.status = envelope_status
    envelope.save()
    transition = services.get_matter_transition_name_by_envelope(
        envelope.matter, 'test'
    )
    assert transition == result_transition


def test_update_matter_status_from_envelope_not_initial(
    matter: Matter, mocker
):
    """Test `update_matter_status_from_envelope` service method.

    Check when `is_initial` flag is set to False on method call, no matter
    `status` updates are made.

    """
    save_matter = mocker.patch('apps.business.models.Matter.save')
    services.update_matter_status_from_envelope(matter, matter.status, False)
    save_matter.assert_not_called()


def test_update_matter_status_from_envelope_the_same_status(
    matter: Matter, mocker
):
    """Test `update_matter_status_from_envelope` service method.

    Check when matter status is not actually changed (should become the same
    as it used to be), no matter `status` updates are made.

    """
    save_matter = mocker.patch('apps.business.models.Matter.save')
    services.update_matter_status_from_envelope(matter, matter.status, True)
    save_matter.assert_not_called()


def test_update_matter_status_from_envelope(matter: Matter, mocker):
    """Test `update_matter_status_from_envelope` service method.

    Check when matter status is really changed and `is_initial` flag is set to
    True, matter `status` updates are performed.

    """
    matter.status = Matter.STATUS_OPEN
    matter.save()

    save_matter = mocker.patch('apps.business.models.Matter.save')
    services.update_matter_status_from_envelope(
        matter, Matter.STATUS_OPEN, True
    )
    save_matter.assert_called()


def test_clean_up_removed_in_docusign_envelopes_from_db_no_exceptions(
    envelope, mocker
):
    """Test `clean_up_removed_in_docusign_envelopes_from_db` exceptions.

    Check method behavior when no exception is raised - no envelope deletion
    should be performed.

    """
    mocker.patch(
        'apps.esign.adapters.DocuSignAdapter.__init__',
        return_value=None
    )
    get_envelope_edit_link = mocker.patch(
        'apps.esign.adapters.DocuSignAdapter.get_envelope_edit_link',
        return_value=None
    )
    delete_envelope = mocker.patch(
        'apps.esign.models.Envelope.delete', return_value=None
    )

    # check envelope that all required methods were called
    services.clean_up_removed_in_docusign_envelopes_from_db(envelope)
    get_envelope_edit_link.assert_called()
    delete_envelope.assert_not_called()


def test_clean_up_removed_in_docusign_envelopes_from_db_another_exception(
    envelope, mocker
):
    """Test `clean_up_removed_in_docusign_envelopes_from_db` exceptions.

    Check method behavior when another (not `NoEnvelopeExistsException`)
    exception is raised - no envelope deletion should be performed.

    """
    mocker.patch(
        'apps.esign.adapters.DocuSignAdapter.__init__',
        return_value=None
    )
    get_envelope_edit_link = mocker.patch(
        'apps.esign.adapters.DocuSignAdapter.get_envelope_edit_link',
        side_effect=Exception
    )
    delete_envelope = mocker.patch(
        'apps.esign.models.Envelope.delete', return_value=None
    )

    # check envelope that all required methods were called
    services.clean_up_removed_in_docusign_envelopes_from_db(envelope)
    get_envelope_edit_link.assert_called()
    delete_envelope.assert_not_called()


def test_clean_up_removed_in_docusign_envelopes_from_db_valid(
    envelope, mocker
):
    """Test `clean_up_removed_in_docusign_envelopes_from_db` exceptions.

    Check method behavior when `NoEnvelopeExistsException` exception is
    raised - envelope deletion should be performed and matter should be moved
    to `draft` status.

    """
    mocker.patch(
        'apps.esign.adapters.DocuSignAdapter.__init__',
        return_value=None
    )
    get_envelope_edit_link = mocker.patch(
        'apps.esign.adapters.DocuSignAdapter.get_envelope_edit_link',
        side_effect=exceptions.NoEnvelopeExistsException
    )
    delete_envelope = mocker.patch('apps.esign.models.Envelope.delete')

    # check envelope that all required methods were called
    services.clean_up_removed_in_docusign_envelopes_from_db(envelope)
    get_envelope_edit_link.assert_called()
    delete_envelope.assert_called()


def test_clean_up_removed_in_docusign_envelopes_from_db_make_draft(
    envelope, mocker
):
    """Test `clean_up_removed_in_docusign_envelopes_from_db` `make_draft`.

    Check that for `initial` envelope, when it's matter not in `draft` state
    `make_draft` method is called.

    """
    mocker.patch(
        'apps.esign.adapters.DocuSignAdapter.__init__',
        return_value=None
    )
    mocker.patch(
        'apps.esign.adapters.DocuSignAdapter.get_envelope_edit_link',
        side_effect=exceptions.NoEnvelopeExistsException
    )
    mocker.patch('apps.esign.models.Envelope.delete')
    make_matter_draft = mocker.patch('apps.business.models.Matter.make_draft')

    # check that for `extra` envelope `make_draft` wasn't called
    envelope.type = models.Envelope.TYPE_EXTRA
    services.clean_up_removed_in_docusign_envelopes_from_db(envelope)
    make_matter_draft.assert_not_called()

    # check for `initial` envelope and `open` matter
    envelope.type = models.Envelope.TYPE_INITIAL
    envelope.matter.status = models.Matter.STATUS_OPEN
    services.clean_up_removed_in_docusign_envelopes_from_db(envelope)
    make_matter_draft.assert_not_called()

    # check for `initial` envelope and `open` matter
    envelope.type = models.Envelope.TYPE_INITIAL
    envelope.matter.status = models.Matter.STATUS_OPEN
    services.clean_up_removed_in_docusign_envelopes_from_db(envelope)
    make_matter_draft.assert_called()
