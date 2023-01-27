import os

import django as original_django

from click import confirm
from invoke import task

from . import django
from .common import print_success
from .credentials_tools import (
    get_credentials_from_vault,
    get_vault_credentials_from_console,
)

##############################################################################
# Data generation for database
##############################################################################

__all__ = (
    'sync_from_remote',
    'fill_sample_data',
)


@task
def sync_from_remote(
    context, environment='develop', db_downloaded=False
):
    """
    Sync data from development DB -> Local DB (remote sync)

    This should connect to development server environment and sync remote
    DB with local DB completely overwriting local data. This is helpful
    for new developers joining to project during its maintenance phase and
    allows easier sync of the data to local DB. Local DB's data will be
    overwritten.

    """
    print_success('Sync from remote database')
    if not confirm(
        f'Do you want to sync with {environment} DB?\n'
        'Warning: this will take 20 ~ 25 minutes\n'
        'This will overwrite your local DB data'
    ):
        return
    dump_name = f'{environment}_db_dump'

    if not db_downloaded:
        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE", "config.settings.local"
        )
        original_django.setup()
        db_config = get_db_config(context, environment)
        get_dump_command = (
            'PGPASSWORD=${DB_PASSWORD} '
            'pg_dump --no-owner '
            '--dbname=${DB_NAME} --host=${DB_HOST} '
            '--port=${DB_PORT} --username=${DB_USER} '
            f'--file {dump_name}.sql'
        )
        print_success(
            f'Getting {environment} db dump. This can take a while.'
        )
        context.run(command=get_dump_command, env=db_config)

    print_success('Resetting local db')
    django.manage(context, 'drop_test_database --noinput')
    django.manage(context, 'reset_db -c --noinput')

    print_success(f'Loading {environment} data')
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'
    from django.conf import settings

    db_settings = settings.DATABASES['default']

    db_config = dict(
        DB_HOST=db_settings['HOST'],
        DB_NAME=db_settings['NAME'],
        DB_PASSWORD=db_settings['PASSWORD'],
        DB_PORT=db_settings['PORT'],
        DB_USER=db_settings['USER'],
    )
    load_dump_command = (
        'PGPASSWORD=${DB_PASSWORD} '
        'psql --quiet '
        '--dbname=${DB_NAME} --host=${DB_HOST} '
        '--port=${DB_PORT} --username=${DB_USER} '
        f'-f {dump_name}.sql'
    )
    context.run(load_dump_command, env=db_config)
    print_success('DB is ready for use')


def get_db_config(context, environment) -> dict:
    """Get database configuration from vault."""
    vault_credentials = get_vault_credentials_from_console(context)

    project_name = f'jlp-backend-{environment}'

    credentials = get_credentials_from_vault(
        **vault_credentials,
        project_name=project_name
    )
    return dict(
        DB_HOST=credentials['DB_HOST'],
        DB_NAME=credentials['DB_NAME'],
        DB_PASSWORD=credentials['DB_PASSWORD'],
        DB_PORT=credentials['DB_PORT'],
        DB_USER=credentials['DB_USER'],
    )


@task
def fill_sample_data(
    context,
    script='fill_sample_data',
    script_args='--silent'
):
    """Fill database with sample data."""
    return django.manage(
        context,
        'runscript {} {}'.format(script, script_args)
    )
