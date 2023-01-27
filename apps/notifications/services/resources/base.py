import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from django.template import Context, Template
from django.template.loader import render_to_string

from libs.utils import get_base_url

from ....core.models import BaseModel
from ... import models

logger = logging.getLogger('django')


class BaseNotificationResource:
    """Base notification class.

    This class is used for creating data representation for notifications.

    Attributes:
        signal (class): A signal to which notification responds
        instance_type (class): Model class with which resource can work with
        notification_type (NotificationType): Type of notification
        runtime_tag (str): runtime_tag of notification type
        instance (BaseModel):
            The one that triggered notification.(Usually it's instance of
            models like Event, Matter, MatterPost)
        recipients(QuerySet):
            Queryset of AppUsers(extracted for instance) who will receive
            notifications (depending on settings)
        title (str):
            Notification's title
        web_content_template (str):
            Path for notification content template that will be used by
            frontend team
        push_content_template(str):
            Path for push notification's template. Used in push
            notifications send by firebase
        email_subject_template(str): Template for creating email subject text
        email_content_template(str):
            Path to html template for email notification's content. Used for
            creating html content for email notifications

    """
    signal = None
    instance_type = None
    runtime_tag: str = None
    title: str = None
    web_content_template: str = None
    push_content_template: str = None
    email_subject_template: str = None
    email_content_template: str = None
    deep_link_template: str = None
    id_attr_path: str = None

    def __init__(self, instance: BaseModel, **kwargs):
        """Initialize notification resource."""
        self.notification_type = models.NotificationType.objects.get(
            runtime_tag=self.runtime_tag
        )
        if not isinstance(instance, self.instance_type):
            raise TypeError(
                f'Resource `{self.__class__.__name__}` can only work with '
                f'`{self.instance_type.__name__}` model'
            )
        self.instance: BaseModel = instance
        self.recipients = self.get_recipients()

    def get_recipients(self) -> QuerySet:
        """Get notification recipients from instance."""
        raise NotImplementedError

    def get_notification_extra_payload(self) -> dict:
        """Get notification's extra payload."""
        return {}

    @classmethod
    def get_deep_link(cls, payload: dict) -> str:
        """Create deep link."""
        return cls.deep_link_template.format(
            base_url=get_base_url(),
            id=getattr(payload['instance'], cls.id_attr_path)
        )

    @classmethod
    def prepare_payload(
        cls,
        notification: models.Notification,
        **kwargs
    ) -> dict:
        """Prepare notification payload for templates."""
        payload = dict(
            notification_type=notification.type,
        )
        if notification.extra_payload:
            payload.update(**notification.extra_payload)
        try:
            instance = notification.content_object
            # if instance is None, try to get it manually from db
            if not instance:
                instance = notification.content_type.get_object_for_this_type(
                    pk=notification.object_id
                )
            payload['instance'] = instance
        except ObjectDoesNotExist:
            logger.warning(
                "Notification trigger object doesn't exist"
            )
            payload['instance'] = None
        payload.update(**kwargs)
        payload['deep_link'] = cls.get_deep_link(payload)
        return payload

    @classmethod
    def render_template(
        cls,
        notification: models.Notification,
        template: str,
        is_file=True,
        **kwargs
    ) -> str:
        """Render template based on notification payload.

        Set is_file = False, if passing str template(not path to the template)

        """
        payload = cls.prepare_payload(notification, **kwargs)
        if is_file:
            return render_to_string(
                template_name=template,
                context=payload
            ).strip()
        context = Context(payload)
        return Template(template).render(context=context).strip()

    @classmethod
    def get_web_notification_content(
        cls, notification: models.Notification, **kwargs
    ) -> str:
        """Get notification content(message) for web notification."""
        return cls.render_template(
            notification=notification,
            template=cls.web_content_template,
            **kwargs,
        )

    @classmethod
    def get_push_notification_content(
        cls, notification: models.Notification, **kwargs
    ) -> str:
        """Get notification content(message) for push notification."""
        return cls.render_template(
            notification=notification,
            template=cls.push_content_template,
            **kwargs,
        )

    @classmethod
    def get_email_subject(
        cls, notification: models.Notification, **kwargs
    ) -> str:
        """Get email subject text."""
        return cls.render_template(
            notification=notification,
            template=cls.email_subject_template,
            is_file=False,
            **kwargs,
        )

    @classmethod
    def get_email_notification_content(
        cls, notification: models.Notification, **kwargs
    ) -> str:
        """Get notification content(message) for email notification."""
        return cls.render_template(
            notification=notification,
            template=cls.email_content_template,
            **kwargs,
        )
