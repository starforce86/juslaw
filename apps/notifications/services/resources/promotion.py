from django.db.models import QuerySet

from ....core.models import BaseModel
from ....promotion import models as promotion_models
from ....promotion import signals as promotion_signals
from ....users import models as user_models
from .base import BaseNotificationResource


class NewAttorneyEventNotificationResource(BaseNotificationResource):
    """Notification class for Attorney events.

    This notification is sent to attorneys' followers, when attorney creates
    new event.

    Recipients: Only client

    In designs it's `New Event` notification type of group
    'Attorneys I Follow'.

    """
    signal = promotion_signals.new_attorney_event
    instance_type = promotion_models.Event
    runtime_tag = 'new_attorney_event'
    title = 'New attorney event'
    deep_link_template = '{base_url}/attorneys/profile/{id}'
    id_attr_path: str = 'attorney_id'
    web_content_template = (
        'notifications/promotion/new_event/web.txt'
    )
    push_content_template = 'notifications/promotion/new_event/push.txt'
    email_subject_template = (
        'New event added by {{instance.attorney.display_name}}'
    )
    email_content_template = 'notifications/promotion/new_event/email.html'

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = instance.attorney.user
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get attorneys' followers."""
        return self.instance.attorney.followers.all()
