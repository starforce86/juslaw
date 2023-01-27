from django.conf import settings


def assert_not_testing(func):
    """Decorator checks that no real API calls are made

    Should be used in another APIs clients, to raise error in case of real API
    calls in testing

    """

    def _wrapped(*args, **kwargs):
        if settings.TESTING:
            raise RuntimeError('Real API requests during testing')
        return func(*args, **kwargs)
    return _wrapped
