from functools import partial

from invoke import Exit, UnexpectedExit, task

from . import is_local_python, start
from .common import print_success

##############################################################################
# Linters
##############################################################################

__all__ = (
    'all',
    'all_git_staged',
    'flake8',
    'isort',
    'isort_check'
)

DEFAULT_FOLDERS = 'apps libs provision'
EXCLUDE = ['migrations/', 'config/']


@task
def all(context, path=DEFAULT_FOLDERS):
    """Run all linters (flake8 and isort).

    Args:
        context: Invoke's context
        path(str): Path to selected file

    Usage:
        # is simple mode without report
        inv linters.all
        # usage on selected file
        inv linters.all --path='apps/users/models.py'

    """
    print_success("Linters: running all linters")
    linters = (isort_check, flake8)
    check_passed = True
    for linter in linters:
        try:
            linter(context, path)
        except UnexpectedExit:
            check_passed = False
    if not check_passed:
        raise Exit(code=1)


@task
def all_git_staged(context):
    """Check only changed files according to git."""
    git_command = 'git diff --staged --name-only HEAD | grep .py'
    exclude_filter = ' | '.join(
        f'grep -v "{to_exclude}"' for to_exclude in EXCLUDE
    )
    git_command = f'{git_command} | {exclude_filter}'
    try:
        context.run(f'{git_command}')
    except UnexpectedExit:
        print_success("Linters: No files to be checked")
        return
    all(context, path=f'$({git_command})')


@task
def flake8(context, path=DEFAULT_FOLDERS):
    """Check code style by `flake8`.

    Args:
        context: Invoke's context
        path(str): Path to selected file
    Usage:
        # is simple mode without report
        inv linters.flake8
        # usage on selected file
        inv linters.flake8 --path='apps/users/models.py'
    """
    print_success("Linters: flake8 running")
    execute = context.run if is_local_python else partial(
        start.run_web, context=context
    )
    return execute(
        command=f'flake8 {path if path else DEFAULT_FOLDERS}'
    )


@task
def isort(context, path=DEFAULT_FOLDERS, params=''):
    """Sorts python imports by the specified path

    Args:
        context: Invoke's context
        params(str): Parameters for command
        path(str): Path to selected file

    Usage:
        # is simple mode without report
        inv linters.isort
        # usage on selected file
        inv linters.isort --path='apps/users/models.py'
    """
    execute = context.run if is_local_python else partial(
        start.run_web, context=context
    )
    return execute(command=f'isort {path} {params}')


@task
def isort_check(context, path=DEFAULT_FOLDERS):
    """Command to fix imports formatting."""
    print_success("Linters: isort running")
    return isort(context, path=path, params='--check-only')
