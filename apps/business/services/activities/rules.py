import typing
from collections import Iterable
from typing import Any

from django.db.models.signals import Signal

from libs.utils import get_lookup_value

from apps.users.models import AppUser

from ... import models

__all__ = (
    'ActivityRule',
    'create_activity',
)


class ActivityRule:
    """Class to remember info about Activity related signal.

    Attributes:
        sender (Signal) - signal which initiates activity creation
        model (Model) - model, which signal initiates activity creation
        msg_template (str) - template of an `activity` message
        get_user_from_signal (bool) - flag which designates whether the user
            will be taken from signal `kwargs`
        related_user_method (Callable) - method to get related to activity user
        related_user_lookup (str) - lookup to activity instance's related user
        checks (Iterable[Callable]) - iterable amount of methods with checks
            that validate if activity should be created
        matter_lookup (str) - lookup to instance's related matter

    It is better to define only one of `related_user_method` or
    `related_user_lookup`. In case if both attributes are set there will be
    taken `related_user_method` by default.

    """
    sender = None
    model = None
    msg_template = None
    get_user_from_signal = False
    related_user_method = None
    related_user_lookup = None
    matter_lookup = None
    checks = []
    user = None
    type = None

    def __init__(
        self, sender: Signal, model: Any, msg_template: str = None,
        get_user_from_signal: bool = False,
        related_user_method: typing.Callable = None,
        related_user_lookup: str = None, checks: Iterable = None,
        matter_lookup: str = None, type: str = None
    ) -> None:
        """Initialize main activity rule info."""
        self.sender = sender or self.sender
        self.model = model or self.model
        self.type = type or self.type
        self.msg_template = msg_template or self.msg_template
        self.get_user_from_signal = get_user_from_signal or self.get_user_from_signal  # noqa
        self.related_user_method = related_user_method or self.related_user_method  # noqa
        self.related_user_method = related_user_method or self.related_user_method  # noqa
        self.related_user_lookup = related_user_lookup or self.related_user_lookup  # noqa
        self.checks = checks or self.checks
        self.matter_lookup = matter_lookup or self.matter_lookup

    def get_rule_user(self, instance: Any) -> AppUser:
        """Shortcut to get `activity` related user."""
        # get rule related user with method if it is defined
        if self.related_user_method:
            return self.related_user_method(instance)
        # otherwise get user with instance lookups
        return get_lookup_value(instance, self.related_user_lookup)

    def get_rule_matter(self, instance: Any, **kwargs) -> models.Matter:
        """Shortcut to get `activity` related matter."""
        if not self.matter_lookup:
            return instance
        return get_lookup_value(instance, self.matter_lookup)

    def get_activity_msg(self, instance: Any, **kwargs) -> str:
        """Method to get `activity` message from template and required params.
        """
        if self.get_user_from_signal:
            user = kwargs.get('user')
        else:
            user = self.get_rule_user(instance)
        return self.msg_template.format(user=user.display_name if user else '')


def create_activity(instance: Any, rule: ActivityRule, **kwargs):
    """Shortcut to create new `Activity` based on Activity Rule."""
    # make all checks before real activity generation
    for check in rule.checks:
        is_succeed = check(instance, **kwargs)
        if not is_succeed:
            return
    activity = models.Activity.objects.create(
        matter=rule.get_rule_matter(instance, **kwargs),
        title=rule.get_activity_msg(instance, **kwargs),
        user=rule.get_rule_user(instance),
        type=rule.type
    )
    return activity
