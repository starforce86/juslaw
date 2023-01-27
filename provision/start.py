from . import docker, is_local_python

##############################################################################
# Run commands
##############################################################################

__all__ = (
    'run_web',
    'run_web_python',
    'run_local_python',
)

wait_for_it_script = './wait-for-it.sh postgres:5432 -- '


def run_web(context, command, watchers=()):
    """Run command in``web`` container.

    docker-compose run --rm web <command>
    """
    return docker.docker_compose_run(
        context,
        params='--rm --service-ports',
        container='web',
        command=command,
        watchers=watchers
    )


def run_web_python(context, command, watchers=()):
    """Run command using web python interpreter"""
    cmd = f'{wait_for_it_script} python3 {command}'
    return run_web(context, cmd, watchers=watchers)


def run_local_python(context, command, watchers=()):
    """Run command using local python interpreter"""
    cmd = f'{wait_for_it_script} python3 {command}'
    return context.run(cmd, watchers=watchers)


if is_local_python:
    run_python = run_local_python
else:
    run_python = run_web_python
