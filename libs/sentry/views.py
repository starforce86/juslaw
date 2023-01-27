from django.shortcuts import render

from sentry_sdk import last_event_id


def handler500(request, *args, **argv):
    """Show custom 500 error page with sentry report form.

    Usage:
        Just simply add this in your url settings:
        handler500 = 'libs.sentry.views.handler500'

    """
    return render(
        request,
        '500.html',
        {'sentry_event_id': last_event_id()},
        status=500
    )
