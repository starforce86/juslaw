EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
CELERY_EMAIL_BACKEND = 'sgbackend.SendGridBackend'
DEFAULT_FROM_EMAIL = 'JusLaw <no-reply@juslaw.com>'
