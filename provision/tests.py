from functools import partial

from invoke import task

from . import is_local_python, start
from .common import print_success

##############################################################################
# Test commands
##############################################################################

__all__ = (
    'run',
    'run_fast',
    'run_full',
    'coverage',
)


@task
def run(context, path='', p=''):
    """Run django tests with ``extra`` args for ``p`` tests.

    `p` means `params` - extra args for tests

    pytest <extra>
    """
    print_success("Tests {} running ".format(path))
    execute = context.run if is_local_python else partial(
        start.run_web, context=context)
    execute(command=' '.join(['pytest', path, p]))


@task
def run_fast(context, path=''):
    """Run django tests as fast as possible.

    No migrations, keep DB.

    pytest --reuse-db -x -q -n 4
    """
    run(context, path=path, p='--reuse-db -x -q -n auto')


@task
def run_full(context):
    """Run all django tests and style tests without cache.

    pytest --create-db --cache-clear -n 4
    """
    run(context, path='', p='--create-db --cache-clear -n auto')


@task
def coverage(context, extra='--reuse-db -n auto'):
    """Generate and display test-coverage"""
    print_success("Calculate and display code coverage")
    execute = context.run if is_local_python else partial(
        start.run_web, context=context)

    execute(command=' '.join(['pytest --cov --cov-report=html', extra]))
    context.run('xdg-open htmlcov/index.html & sleep 3')
