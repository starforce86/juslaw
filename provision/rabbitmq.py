from invoke import task

from . import docker
from .common import print_success

__all__ = ('add_local_virtualhost',)


def init(context):
    """Create virtualhost in rabbitmq and grants permissions
    """
    print_success("Initial configuration for rabbitmq")
    docker.docker_compose_exec(
        context,
        'rabbitmq', 'rabbitmqctl add_vhost "jlp-development"')  # noqa
    docker.docker_compose_exec(
        context,
        'rabbitmq', 'rabbitmqctl add_user jlp_user manager')  # noqa
    docker.docker_compose_exec(
        context,
        'rabbitmq',
        'rabbitmqctl set_permissions -p "jlp-development" jlp_user ".*" ".*" ".*"')  # noqa


@task
def add_local_virtualhost(context):
    """Create virtualhost in rabbitmq and grants permissions for local env."""
    print_success("Local configuration for rabbitmq")
    docker.docker_compose_exec(
        context,
        'rabbitmq', 'rabbitmqctl add_vhost "jlp-local"')
    docker.docker_compose_exec(
        context,
        'rabbitmq',
        'rabbitmqctl set_permissions -p "jlp-local" jlp_user ".*" ".*" ".*"')
