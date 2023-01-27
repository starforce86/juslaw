from invoke import task

from . import docker, is_local_python
from .common import print_error

__all__ = (
    'beat',
    'worker',
    'flower',
)


@task()
def beat(context):
    """Start celery beat."""
    if is_local_python:
        context.run('celery beat --app config.celery:app -l info -S django')
    else:
        docker.up_containers(context, containers=['celery_beat'])


@task()
def worker(context):
    """Start celery worker."""
    if is_local_python:
        context.run('celery worker --app config.celery:app -l info')
    else:
        docker.up_containers(context, containers=['celery_worker'])


@task()
def flower(context):
    """Start celery flower."""
    if is_local_python:
        context.run(
            'celery flower --app config.celery:app '
            '--address=127.0.0.1 --port=5555'
        )
    else:
        print_error('Not supported')
