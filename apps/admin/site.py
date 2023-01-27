from functools import update_wrapper

from django.contrib.admin import AdminSite as DjangoAdminSite
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache

from constance import config

from .export.statistics import AppStatisticsResource
from .services import get_apps_stats


class AdminSite(DjangoAdminSite):
    """Our custom admin site.

    Extended to customize index view. In index view we added statistics
    dashboard, with statistics export button.

    """

    # Text to put at the end of each page's <title>.
    site_title = _(f'{config.APP_LABEL} Administration')

    # Text to put in each page's <h1>.
    site_header = _(f'{config.APP_LABEL} Administration')

    @never_cache
    def index(self, request, extra_context: dict = None):
        """ Display the main admin index page,

        Index lists all of the installed apps that have been registered in
        this site. Also shows minor statistics.

        """
        if not extra_context:
            extra_context = {}
        extra_context.update(**get_apps_stats())
        extra_context['app_label'] = config.APP_LABEL

        return super().index(request, extra_context)

    @never_cache
    def export_dashboard_statistics(self, request):
        """Download file with dashboard stats."""
        resource = AppStatisticsResource()
        data = resource.export()
        response = resource.get_export_file_response(data=data)
        return response

    def get_urls(self):
        """Extend to add extra urls for admin app."""

        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            wrapper.admin_site = self
            return update_wrapper(wrapper, view)

        urlpatterns = super().get_urls()
        urlpatterns.append(
            path(
                'export_dashboard_statistics',
                wrap(self.export_dashboard_statistics),
                name='export_dashboard_statistics'
            ),
        )
        return urlpatterns
