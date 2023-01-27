from invoke import task

from .common import print_success


class InvokeNetworkException(Exception):
    """Docker networking exception

    Used to bypass fatal error of invoke cli execution
    in the case desired docker network is already created
    """
    pass


##############################################################################
# Containers start stop commands
##############################################################################


__all__ = (
    'stop',
    'up',
    'up_containers',
    'stop_containers',
    'docker_compose_run',
)


def docker_compose_run(
    context, params: str, container: str, command: str, watchers=()
):
    """Run ``command`` using docker-compose

    docker-compose run <params> <container> <command>
    Start container and run command in it.

    Used function so lately it can be extended to use different docker-compose
    files.

    Args:
        context: invoke context
        params: configuration params for docker compose
        container: name of container to start
        command: command to run in started container
        watchers: Automated responders to command

    """
    cmd = f'docker-compose run {params} {container} {command}'
    return context.run(cmd, watchers=watchers)


def docker_compose_exec(context, service: str, command: str):
    """Run ``exec`` using docker-compose

    docker-compose exec <service> <command>
    Run commands in already running container.

    Used function so lately it can be extended to use different docker-compose
    files.

    Args:
        context: invoke context
        service: name of service to run command in
        command: command to run in service container

    """
    cmd = f'docker-compose exec {service} {command}'
    return context.run(cmd)


def up_containers(context, containers, **kwargs):
    """Bring up containers and run them.

    Add `d` kwarg to run them in background.

    """
    print_success(f"Bring up {' '.join(containers)} containers ")
    cmd = (
        f"docker-compose up "
        f"{'-d ' if kwargs.get('d') else ''}"
        f"{' '.join(containers)}"
    )
    context.run(cmd)


def stop_containers(context, containers):
    """Stop containers."""
    print_success(f"Stopping {' '.join(containers)} containers ")
    cmd = f"docker-compose stop {' '.join(containers)}"
    context.run(cmd)


##############################################################################
# Containers networking
##############################################################################

def create_network(context, network=None):
    """Create docker network
    """
    if not network:
        return None

    print_success("Create {} network".format(network))

    try:
        context.run(
            'docker network create {}'.format(network),
            warn=True,
        )
    except InvokeNetworkException:
        pass


@task
def up(context):
    """Bring up main containers and start them."""
    up_containers(
        context,
        containers=['postgres', 'rabbitmq', 'redis', ],
        d=True,
    )


@task
def stop(context):
    """Stop main containers."""
    stop_containers(
        context,
        containers=['postgres', 'rabbitmq', 'redis', ]
    )


@task
def clear(context):
    """Stop and remove all containers defined in docker-compose.

    Also remove images.

    """
    print_success('Clearing docker-compose')
    context.run('docker-compose rm -f')
    context.run('docker-compose down -v --rmi all --remove-orphans')
    pull(context)


@task
def pull(context):
    """Pull all images defined in docker-compose."""
    print_success('Pulling docker images')
    context.run('docker-compose pull')
