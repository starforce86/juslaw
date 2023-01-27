import logging
from typing import List

from docusign_esign import EnvelopeEvent, EventNotification

from .constants import ENVELOPE_STATUS_CREATED, ENVELOPE_STATUS_SIGNED

__all__ = (
    'get_envelope_status_notification',
)

logger = logging.getLogger('docusign')


def get_envelope_status_notification(
    statuses: List[str], webhook_url: str
) -> EventNotification:
    """Generate notification from DocuSign on Envelope status changes.

    Method is a shortcut which generates notification about all statuses
    changes.

    It is not allowed to create event notifications on `created`
    and `signed` statuses in DocuSign API.

    Attributes:
        statuses (list) - list of statuses for which envelope's event
            notifications should be generated
        webhook_url (str) - url to which DocuSign will make webhooks on
            envelope status update

    Returns:
        (EventNotification) - configured notification object, which will
            trigger backend api on any Envelope status change.

    """
    track_statuses = set(statuses) - \
        set([ENVELOPE_STATUS_CREATED, ENVELOPE_STATUS_SIGNED])
    return EventNotification(
        logging_enabled=True,
        require_acknowledgment=True,
        include_envelope_void_reason=True,
        url=webhook_url,
        envelope_events=[
            EnvelopeEvent(envelope_event_status_code=status)
            for status in track_statuses
        ]
    )
