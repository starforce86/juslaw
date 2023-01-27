from typing import List

from django.db.models import DecimalField, Q
from django.db.models.expressions import Func

from ...business import models
from ...documents.models import Folder
from ...users.models import AppUser, Invite
from ...users.utils import send_invitation


def get_matter_shared_folder(matter: models.Matter) -> Folder:
    """Get matter's shared folder."""
    return matter.folders.get(is_shared=True)


def share_matter(
    user: AppUser, matter: models.Matter, title: str, message: str,
    emails: List[str] = None, users: List[AppUser] = None
):
    """Common method to initiate matter's sharing."""
    if emails:
        share_matter_by_invite(user, matter, title, message, emails)

    if users is not None:
        share_matter_with_users(user, matter, title, message, users)

    return matter


def share_matter_by_invite(
    user: AppUser, matter: models.Matter, title: str, message: str,
    emails: List[str] = None
):
    """Share matter with new users by `invites`.

    This method creates a new `invite` from matter's attorney and remembers
    which matter should be shared with user after his registration.

    Arguments:
        user (AppUser): user that shared matter
        matter (Matter): matter that should be shared with users
        title (str): title of a sent to users email message
        message (str): body of a sent to users message
        emails (str): list of users emails with which matter should be shared
            after their registration

    """
    invites = Invite.objects.bulk_create(
        Invite(
            inviter=user,
            title=title,
            message=message,
            matter=matter,
            email=email,
            user_type=Invite.USER_TYPE_ATTORNEY
        ) for email in emails
    )
    # call `send_invitation` for each created invite cause `post_save` signal
    # is not called on bulk action
    for invite in invites:
        send_invitation(invite)


def share_matter_with_users(
    user: AppUser, matter: models.Matter, title: str, message: str,
    users: List[AppUser] = None
):
    """Share matter with app users.

    Users existing in `users` with which matter was already shared before -
    ignored. Users absent in `users` with which matter was already shared
    before - removed. New users in `users` are added.

    When matter is shared with users:

        1. These users will have the same permissions for matter as
        original owner.

        2. There is sent an notification for each user that matter
        was shared.

    Arguments:
        user (AppUser): user that shared matter
        matter (Matter): matter that should be shared with users
        title (str): title of a sent to users notification
        message (str): body of a sent to users notification
        users (AppUser): list of users with which matter is shared
        user_type (str): type of users with which matter suppose to be shared

    Depending on `user_type` there would be considered what kind of users would
    be added/removed to/from `shared_with` field. For example:

        - if `user_type=attorney` - there would be taken only `attorneys` users
        from input `users` data and matter's `shared_with` field (all
        `paralegal` users in matter's `shared_with` will remain untouched as
        far as `paralegal` users from `users` input data would be ignored)

        - if `user_type=paralegal` - there would be taken only `paralegal`
        users from input `users` data and matter's `shared_with` field (all
        `attorney` users in matter's `shared_with` will remain untouched as far
        as `attorney` users from `users` input data would be ignored)

    """
    from ...business.signals import new_matter_shared

    users = filter(lambda us: us.is_attorney or us.is_paralegal, users)
    already_shared = matter.shared_with.filter(
        Q(attorney__isnull=False) | Q(paralegal__isnull=False)
    )

    users = set([us.pk for us in users]) if users else set()
    already_shared = set(already_shared.values_list('pk', flat=True))

    # exclude also matter owner if he was suddenly passed
    to_create = users - already_shared - {matter.attorney.user_id}
    # to_remove = already_shared - users

    # remove redundant anymore attorneys
    # models.MatterSharedWith.objects.filter(
    #     matter=matter,
    #     user__id__in=to_remove
    # ).delete()

    if not to_create:
        return

    # create `MatterSharedWith` links
    matters_shared = models.MatterSharedWith.objects.bulk_create(
        models.MatterSharedWith(matter=matter, user_id=user_id)
        for user_id in to_create
    )
    for matter_shared in matters_shared:
        # Notify attorneys and supports that user shared matter with them
        new_matter_shared.send(
            sender=models.MatterSharedWith,
            instance=matter_shared,
            inviter=user,
            title=title,
            message=message,
        )


class Epoch(Func):
    template = 'EXTRACT(epoch FROM %(expressions)s)::INTEGER'
    output_field = DecimalField()
