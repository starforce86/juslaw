from django.utils import timezone

from ..users import models, notifications


def send_invitation(invite: models.Invite):
    """Send invitation mail to client."""
    notifications.InviteNotification(invite=invite).send()
    invite.sent = timezone.now()
    invite.save()


def inform_inviter(invite: models.Invite):
    """Send mail to inviter about registered client."""
    notifications.RegisteredClientNotification(invite=invite).send()
