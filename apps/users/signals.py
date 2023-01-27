import os
import typing
from typing import Union

from django.db.models import signals
from django.dispatch import Signal, receiver

from ..business.models import Stage
from ..documents.models import Folder
from ..notifications.models import NotificationSetting
from ..users import models, utils

new_opportunities_for_attorney = Signal(providing_args=('instance',))
new_opportunities_for_attorney.__doc__ = (
    'Signal which indicates that there are new opportunities for attorney'
)
new_registered_contact_shared = Signal(
    providing_args=('instance', 'receiver_pks', )
)

new_registered_contact_shared.__doc__ = (
    'Signal which indicates a new registered '
    'contact(client) has been shared with attorney'
)
new_unregistered_contact_shared = Signal(
    providing_args=('instance', 'receiver_pks', )
)

new_unregistered_contact_shared.__doc__ = (
    'Signal which indicates a new unregistered '
    'contact(invite) has been shared with attorney'
)

attorney_verified = Signal(providing_args=('instance',))
paralegal_verified = Signal(providing_args=('instance',))
enterprise_verified = Signal(providing_args=('instance',))
attorney_verified.__doc__ = (
    'Signal which indicates that attorney was verified'
)
paralegal_verified.__doc__ = (
    'Signal which indicates that paralegal was verified'
)
enterprise_verified.__doc__ = (
    'Signal which indicates that enterprise was verified'
)

new_user_registered = Signal(providing_args=('instance',))
new_user_registered.__doc__ = (
    'Signal which indicates that attorney or enterprise or paralegal '
    'are registered'
)


@receiver(signals.post_save, sender=models.Attorney)
@receiver(signals.post_save, sender=models.Paralegal)
@receiver(signals.post_save, sender=models.Enterprise)
@receiver(signals.post_save, sender=models.Support)
def new_user_profile_for_verification(
    instance: Union[
        models.Attorney, models.Paralegal, models.Enterprise, models.Support
    ],
    created,
    **kwargs
):
    """Notify admins that new attorney/support profile is awaiting verification

    Also make user account inactive until admins verify it.

    """
    if not created:
        return

    instance.register_new_user()
    if isinstance(instance, models.Attorney):
        Stage.create_default_stages(instance)
    if isinstance(instance, models.Attorney) or \
            isinstance(instance, models.Paralegal) or \
            isinstance(instance, models.Enterprise):
        if os.environ.get('ENVIRONMENT', '') == 'prod':
            new_user_registered.send(
                sender=models.AppUser, instance=instance.user
            )


@receiver(signals.post_save, sender=models.Attorney)
@receiver(signals.post_save, sender=models.Paralegal)
@receiver(signals.post_save, sender=models.Enterprise)
@receiver(signals.post_save, sender=models.Support)
def new_user_template_folder(
    instance: Union[
        models.Attorney, models.Paralegal, models.Enterprise, models.Support
    ],
    created,
    **kwargs
):
    """Create folder for templates for new registered attorney/support."""
    if not created:
        return

    Folder.objects.create(
        title='Personal templates', is_template=True, owner_id=instance.pk
    )


@receiver(signals.post_save, sender=models.Invite)
def send_invitation_mail(instance: models.Invite, created, **kwargs):
    """Send invitation email to a user(if user was invited by another user)."""
    if not created or instance.type == models.Invite.TYPE_IMPORTED:
        return

    utils.send_invitation(instance)


@receiver(signals.post_save, sender=models.AppUser)
def set_link_to_user_in_invites(instance: models.AppUser, created, **kwargs):
    """Set in all invites link to a new user with same email."""
    if not created:
        return

    models.Invite.objects.without_user().filter(
        email__iexact=instance.email
    ).update(user=instance)


@receiver(signals.post_save, sender=models.Client)
def inform_inviter_about_user(instance: models.Client, created, **kwargs):
    """Inform attorney that user has been registered."""
    if not created:
        return

    invites = models.Invite.objects.filter(
        email__iexact=instance.email
    )
    for invite in invites:
        utils.inform_inviter(invite=invite)


@receiver(signals.post_save, sender=models.UserStatistic)
def new_opportunities_statistics(
    instance: models.UserStatistic, created, **kwargs
):
    """Send signal that there is new opportunities stat for attorney."""
    is_opportunities_stat = (
        instance.count > 0 and
        instance.tag == models.UserStatistic.TAG_OPPORTUNITIES
    )
    if not created or not is_opportunities_stat:
        return

    new_opportunities_for_attorney.send(
        sender=models.UserStatistic, instance=instance
    )


@receiver(signals.post_save, sender=models.Attorney)
@receiver(signals.post_save, sender=models.Paralegal)
@receiver(signals.post_save, sender=models.Support)
@receiver(signals.post_save, sender=models.Client)
def enable_notifications(
    instance: typing.Union[
        models.Client,
        models.Attorney,
        models.Paralegal,
        models.Support
    ],
    created: bool,
    **kwargs
):
    """Enable all notification for new client, attorney or support."""
    if not created:
        return

    user = instance.user
    NotificationSetting.objects.create(
        user=user, by_email=True, by_push=True
    )


@receiver(signals.m2m_changed, sender=models.Client.shared_with.through)
@receiver(signals.m2m_changed, sender=models.Invite.shared_with.through)
def enable_new_contact_notifications(
    instance: typing.Union[
        models.Client.shared_with.through,
        models.Invite.shared_with.through,
    ],
    **kwargs
):
    user = instance.user
    from apps.business.models import Opportunity
    if user is not None:
        Opportunity.objects.bulk_create(
            [
                Opportunity(
                    client=models.Client.objects.get(user_id=user.id),
                    attorney=models.Attorney.objects.get(user_id=attorney_id)
                )
                for attorney_id in kwargs.get('pk_set')
            ]
        )
    if kwargs.get('pk_set'):
        if isinstance(instance, models.Invite):
            new_unregistered_contact_shared.send(
                sender=models.Invite,
                instance=instance,
                receiver_pks=kwargs.get('pk_set')
            )
        else:
            new_registered_contact_shared.send(
                sender=models.Client,
                instance=instance,
                receiver_pks=kwargs.get('pk_set')
            )
