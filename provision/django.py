import os

from invoke import Responder, task

from . import docker, locations, start, system
from .common import print_error, print_success

##############################################################################
# Django commands and stuff
##############################################################################

__all__ = (
    'manage',
    'makemigrations',
    'check_new_migrations',
    'migrate',
    'resetdb',
    'run',
    'shell',
    'dbshell',
)


@task
def manage(context, command, watchers=()):
    """Run ``manage.py`` command

    docker-compose run --rm web python3 manage.py <command>
    """
    docker.up(context)
    cmd = f'manage.py {command}'
    return start.run_python(context, cmd, watchers=watchers)


@task
def check_new_migrations(context):
    """Check if there is new migrations or not."""
    print_success("Checking migrations")
    manage(context, 'makemigrations --check --dry-run')


@task
def makemigrations(context):
    """Run makemigrations command and chown created migrations."""
    print_success("Django: Make migrations")
    manage(context, 'makemigrations')
    system.chown(context)


@task
def migrate(context):
    """Run ``migrate`` command"""
    print_success("Django: Apply migrations")
    manage(context, 'migrate')


@task
def resetdb(context):
    """Reset database to initial state (including test DB)"""
    print_success("Reset database to its initial state")
    manage(context, 'drop_test_database --noinput')
    manage(context, 'reset_db -c --noinput')
    makemigrations(context)
    migrate(context)
    locations.create_fake_country(context)
    createsuperuser(context)


@task
def createsuperuser(context, email='root@root.com', password='rootroot'):
    """Create superuser."""
    print_success("Create superuser")
    responder_email = Responder(
        pattern=r"E-mail address: ",
        response=email + '\n',
    )
    responder_password = Responder(
        pattern=r"(Password: )|(Password \(again\): )",
        response=password + '\n',
    )
    manage(
        context,
        command='createsuperuser',
        watchers=[responder_email, responder_password]
    )


@task
def run(context):
    """Run development web-server"""

    # start dependencies (so even in local mode this command
    # is working successfully
    # if you need more default services to be started define them
    # below, like celery, etc.
    docker.up(context)
    try:
        env = os.environ["JLP_BACKEND_ENVIRONMENT"]  # noqa
    except KeyError:
        print_error(
            "Please set the environment variable "
            "JLP_BACKEND_ENVIRONMENT, like=local")
        exit(1)
    print_success("Running web app")
    start.run_python(
        context,
        "manage.py runserver_plus 0.0.0.0:8000  --reloader-type stat --pm"
    )


@task
def shell(context, params=None):
    """Shortcut for manage.py shell_plus command

    Additional params available here:
        http://django-extensions.readthedocs.io/en/latest/shell_plus.html
    """
    print_success("Entering Django Shell")
    manage(context, 'shell_plus --ipython {}'.format(params or ""))


@task
def dbshell(context):
    """Open postgresql shell with credentials from either local or dev env"""
    print_success("Entering DB shell")
    manage(context, 'dbshell')
