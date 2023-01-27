from django.db.models import QuerySet

from ....core.models import BaseModel
from ....forums import models as forum_models
from ....forums import signals as forums_signals
from ....users import models as user_models
from .base import BaseNotificationResource


class NewCommentNotificationResource(BaseNotificationResource):
    """Notification class for new posts in followed topic.

    This notification is sent to topic' followers, when somebody creates
    new post in this topic.

    Recipients: Attorneys and clients

    In designs it's `Topics I Follow Activity` notification type

    """
    signal = forums_signals.new_comment_on_post
    instance_type = forum_models.Comment
    # TODO: these template paths and runtime tag
    #  needs to be updated in accordance with new forums system
    runtime_tag = 'new_post'
    title = 'New comment'
    deep_link_template = '{base_url}/forum/post/{id}/0'
    id_attr_path: str = 'post_id'
    web_content_template = (
        'notifications/forums/new_post/web.txt'
    )
    push_content_template = 'notifications/forums/new_comment/push.txt'
    email_subject_template = (
        ' New reply on {{ instance.post.title }}'
    )
    email_content_template = (
        'notifications/forums/new_post/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = instance.author
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get topic followers."""
        return self.instance.post.followers.exclude(
            pk=self.instance.author.pk
        )


class NewAttorneyCommentNotificationResource(BaseNotificationResource):
    """Notification class for Attorney's new comments.

    This notification is sent to attorneys' followers, when attorney creates
    new comment in forums.

    Recipients: Only client

    In designs it's `Forum Activity` notification type of group
    'Attorneys I Follow'.

    """
    signal = forums_signals.new_comment_on_post_by_attorney
    instance_type = forum_models.Comment
    # TODO: these template paths and runtime tag
    #  needs to be updated in accordance with new forums system
    runtime_tag = 'new_attorney_post'
    title = 'New attorney comment'
    deep_link_template = '{base_url}/forum/post/{id}/0'
    id_attr_path: str = 'post_id'
    web_content_template = (
        'notifications/forums/new_attorney_post/web.txt'
    )
    push_content_template = 'notifications/forums/new_attorney_post/push.txt'
    email_subject_template = (
        'Jus-Law - New forum activity from {{ instance.author.display_name }}'
    )
    email_content_template = (
        'notifications/forums/new_attorney_post/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = instance.author
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get attorneys followers."""
        return self.instance.author.attorney.followers.all()


class NewPostNotificationResource(BaseNotificationResource):
    """Notification class new posts on topic.

    This notification is sent topic followers, when new post is created

    Recipients: Attorney, Clients

    """
    signal = forums_signals.new_post_on_topic
    instance_type = forum_models.Post
    runtime_tag = 'new_post_on_topic'
    title = 'New Post'
    deep_link_template = '{base_url}/forum/post/{id}/0'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/forums/new_post_on_topic/web.txt'
    )
    push_content_template = 'notifications/forums/new_post_on_topic/push.txt'
    email_subject_template = (
        'Jus-Law - New Post on topic {{ instance.topic.title }}'
    )
    email_content_template = (
        'notifications/forums/new_post_on_topic/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = instance.author
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get attorneys followers."""
        return self.instance.topic.followers.all()
