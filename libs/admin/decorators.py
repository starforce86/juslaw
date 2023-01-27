from django.conf import settings
from django.contrib import admin


def register_in_debug(*args, **kwargs):
    """Register model admin for debug mode.

    When debug mode is off it returns noting-do wrapper, which returns
    decorated object itself.

    Returns:
        object
    """
    if settings.DEBUG:
        return admin.register(*args, **kwargs)
    else:
        def wrapper(admin_class):
            return admin_class
        return wrapper
