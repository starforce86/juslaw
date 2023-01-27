import arrow

from config.celery import app

from apps.users.models import AppUser, Invite

from . import models, services, signals


@app.task()
def generate_invoices():
    """Celery task to generate Invoice.

    At the 1st day of each new month new `Invoice` is generated for a previous
    month and the task adds all time billings in Invoice period and connects it
    with invoice.

    Invoices are generated only for `hourly` rate typed `active` matters.

    """
    # calculate invoice period
    now = arrow.utcnow().shift(days=-1)
    period_start, period_end = services.get_invoice_period_ranges(now)

    # generate invoices only if there are related time billings
    time_billings = models.BillingItem.objects.all().match_period(
        period_start=period_start,
        period_end=period_end,
    )
    if not time_billings.exists():
        return

    # generate invoices
    matters = models.Matter.objects.open().hourly_rated()
    for matter in matters:
        services.get_invoice_for_matter(matter, period_start, period_end)


@app.task()
def send_shared_matter_notification_task(user_id: int):
    """Send `matter shared` notification when user is registered and verified.

    When user with which matter was shared is registered and verified - send
    matter shared notification to him.

    Method sends only latest invite messages for users that were invited to
    `share matter` few times.

    """
    user = AppUser.objects.get(id=user_id)
    invites = Invite.objects.filter(
        email__iexact=user.email, matter__isnull=False
    ).order_by('-created')
    matters = []
    for invite in invites:
        matter = invite.matter
        # do not process matters for which notifications were already sent
        if matter in matters:
            continue

        matters.append(matter)
        matter_shared, created = models.MatterSharedWith.objects.get_or_create(
            matter=matter, user=user
        )
        if not created:
            continue

        # MatterSharedWith is created, sent notification to attorney and
        # support
        signals.new_matter_shared.send(
            sender=models.MatterSharedWith,
            instance=matter_shared,
            inviter=invite.inviter,
            title=invite.title,
            message=invite.message,
        )
