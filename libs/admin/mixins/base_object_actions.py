from itertools import chain

from django.conf.urls import url

from django_object_actions import DjangoObjectActions
from django_object_actions.utils import ChangeActionView, ChangeListActionView


class BaseObjectActionsMixin(DjangoObjectActions):
    """Mixin which provides functionality of adding `base_change_actions`.
    """
    base_change_actions = []

    def _get_action_urls(self):
        """Register `base_change_actions` urls.

        Almost original method with the change in adding `base_change_actions`
        in 84 line.

        """
        actions = {}

        model_name = self.model._meta.model_name
        # e.g.: polls_poll
        base_url_name = "%s_%s" % (self.model._meta.app_label, model_name)
        # e.g.: polls_poll_actions
        model_actions_url_name = "%s_actions" % base_url_name

        self.tools_view_name = "admin:" + model_actions_url_name

        # WISHLIST use get_change_actions and get_changelist_actions
        # TODO separate change and changelist actions
        # the main change is here - added `base_change_actions` urls and
        # `related_models_change_actions`
        all_actions = chain(
            self.change_actions,
            getattr(self, 'related_models_change_actions', []),
            self.changelist_actions,
            self.base_change_actions
        )
        for action in all_actions:
            actions[action] = getattr(self, action)
        return [
            # change, supports the same pks the admin does
            # https://github.com/django/django/blob/stable/1.10.x/django/
            # contrib/admin/options.py#L555
            url(
                r"^(?P<pk>.+)/actions/(?P<tool>\w+)/$",
                self.admin_site.admin_view(  # checks permissions
                    ChangeActionView.as_view(
                        model=self.model,
                        actions=actions,
                        back="admin:%s_change" % base_url_name,
                        current_app=self.admin_site.name,
                    )
                ),
                name=model_actions_url_name,
            ),
            # changelist
            url(
                r"^actions/(?P<tool>\w+)/$",
                self.admin_site.admin_view(  # checks permissions
                    ChangeListActionView.as_view(
                        model=self.model,
                        actions=actions,
                        back="admin:%s_changelist" % base_url_name,
                        current_app=self.admin_site.name,
                    )
                ),
                # Dupe name is fine. https://code.djangoproject.com/ticket/
                # 14259
                name=model_actions_url_name,
            ),
        ]
