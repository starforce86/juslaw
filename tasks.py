import os
import sys
from importlib import util

from invoke import Collection

from provision import (
    celery,
    credentials_tools,
    data,
    django,
    docker,
    docs,
    git,
    linters,
    locations,
    project,
    rabbitmq,
    system,
    tests,
)

ns = Collection(
    celery,
    credentials_tools,
    data,
    django,
    docker,
    docs,
    git,
    linters,
    locations,
    project,
    rabbitmq,
    system,
    tests,
)

# Configurations for run command
ns.configure({'run': {'pty': True, 'echo': True}})

# let's load custom commands defined in
# ~/.invoke/my.py

sys.path.append(os.path.expanduser('~/.invoke'))

spec = util.find_spec('my')

# load custom invoke commands in the case such
# file exists
if spec:
    zzz = util.module_from_spec(spec)
    spec.loader.exec_module(zzz)
