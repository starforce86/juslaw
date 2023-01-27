import os

from invoke import task

from . import (
    common,
    data,
    django,
    docker,
    git,
    is_local_python,
    rabbitmq,
    tests,
)

##############################################################################
# Build project locally
##############################################################################

__all__ = (
    'build',
    'init',
    'install_tools',
    'install_requirements',
    'install_pytest_plugins',
    'compile_requirements',
    'recompile_rebuild',
    'copy_local',
    'clean_pip',
)


@task()
def copy_local(context, force_update=True):
    """Copy local settings from template

    Args:
        context: invoke context
        force_update(bool): rewrite file if exists or not

    """
    local_settings = 'config/settings/local.py'
    local_template = 'config/settings/local.py.template'

    if force_update or not os.path.isfile(local_settings):
        context.run(
            ' '.join(['cp', local_template, local_settings])
        )

        with open(local_settings, 'r') as f:
            settings = f.read()

        settings = settings.replace(
            '%STRIPE_TEST_PUBLIC_KEY%', 'pk_test_'
        )
        settings = settings.replace(
            '%STRIPE_TEST_SECRET_KEY%', 'sk_test_'
        )
        with open(local_settings, 'w') as f:
            f.write(settings)


@task
def build(context):
    """Build python environ."""
    if is_local_python:
        install_requirements(context)
    else:
        common.print_success("Building docker `web app` container")
        cmd = 'docker-compose build --build-arg DEV_ENVIRONMENT=True web'
        context.run(cmd)


@task
def init(context, clean=False):
    """Build project from scratch"""
    common.print_success('Setting up git')
    git.hooks(context)
    git.gitmessage(context)

    if clean:
        common.print_success('Cleaning up')
        clean_pip(context)
        docker.clear(context)

    common.print_success('Initial assembly of all dependencies')
    install_tools(context)

    common.print_success('Installing requirements')
    install_requirements(context)
    install_pytest_plugins(context)
    docker.pull(context)

    common.print_success('Building project container')
    copy_local(context)
    context.run('invoke credentials-tools.init-settings-local')
    build(context)

    django.makemigrations(context)
    django.migrate(context)
    django.createsuperuser(context)

    rabbitmq.init(context)
    tests.run(context)

    data.fill_sample_data(context)

    common.print_success(
        "Type `JLP_BACKEND_ENVIRONMENT=local inv django.run` to start web app"
    )


##############################################################################
# Manage dependencies
##############################################################################
@task
def install_tools(context):
    """Install shell/cli dependencies, and tools needed to install requirements

    Define your dependencies here, for example
    local('sudo npm -g install ngrok')
    """
    context.run('pip install -U pip setuptools pip-tools')


@task
def install_requirements(context, env='development'):
    """Install local development requirements"""
    common.print_success("Install requirements")
    context.run(f'pip install -r requirements/{env}.txt')


@task
def install_pytest_plugins(context):
    """Install pytest plugins for local development """
    pytest_plugins = (
        'pytest-pycharm pytest-picked pytest-django-queries'
    )
    context.run(f'pip install -U {pytest_plugins}')


@task
def compile_requirements(context, update=False):
    """Recompile dependencies."""
    common.print_success('Compile requirements with pip-compile')
    update = '-U' if update else ''
    envs = (
        'development',
        'staging',
        'production',
    )
    for env in envs:
        common.print_success(f'Compile requirements for {env=}.')
        context.run(f'pip-compile -q requirements/{env}.in {update}')


@task
def recompile_rebuild(context, update=False):
    """Recompile dependencies and re-build docker containers"""
    compile_requirements(context, update=update)
    common.print_success("Rebuild container")
    build(context)


@task
def clean_pip(context, env='development'):
    """Remove all installed dependencies mentioned in requirements."""
    context.run(f'pip uninstall -y -r requirements/{env}.txt')
