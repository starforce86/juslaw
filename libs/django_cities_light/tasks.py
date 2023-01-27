from django.core.management import call_command

from config.celery import app


@app.task()
def update_django_cities_light_db():
    """Update django_cities_light database."""
    # call_command('cities_light', '--progress')
    pass
