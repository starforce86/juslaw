from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

import pytz


class TimezoneMiddleware(MiddlewareMixin):
    """Mixing for middleware to user timezone from request."""

    def process_request(self, request):
        """Update timezone status from request."""
        try:
            tzname = request.META.get('HTTP_USER_TIMEZONE', None)
            if tzname:
                timezone.activate(pytz.timezone(tzname))
                request.timezone = pytz.timezone(tzname)
            else:
                timezone.deactivate()
        except pytz.UnknownTimeZoneError:
            timezone.deactivate()
