import os

from invoke import task

from . import django
from .common import print_success

# -----------------------------------------------------------------------------
# Explanation of cities_light management command
# * Calling cities_light for first time, will download locations files
#   and import location data in to our db. When called for second time it will
#   check downloaded files, it there is update it'll update them and make
#   import.
#   Note: if you reset db and just called cities_light, it won't refill
#   your db with locations
# * --force-import-all will make cities_light to import of locations data from
#   files, but it will not update location files
# * --force-all will re-download locations files and do import of locations
#   data from downloaded files
# Explanation of cities_light's import process: From what i could understand it
# goes this way: For example cities, it first tries to find cities by
# geoname_id. If it fails it creates new entry, else it updates found entry. It
# doesn't delete entries.
# -----------------------------------------------------------------------------

__all__ = (
    'load_locations',
    'create_fake_country'
)


@task
def create_fake_country(context):
    """Create fake country, can be used instead of load_locations."""
    print_success("Creating fake country")
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'

    django.manage(context, 'create_fake_country')


@task
def load_locations(context, params='--force-import-all --progress'):
    """Load django_cities_light database.

    params:
        --force-import-all - Import data even if files are up-to-date.
        --force-all - Download and import data.
        --progress - Show progress bar
    """
    print_success("Updating cities_light db")
    django.manage(context, f'cities_light  {params}')
