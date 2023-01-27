# All this methods are copied from CheckMixin from django_health_check,
# but only slightly edited

import copy
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Iterable, Tuple

from health_check.plugins import plugin_dir

from .backends.base import AbstractHealthCheckBackend


def get_plugins(
    plugins_list: Iterable[str]
) -> Tuple[AbstractHealthCheckBackend]:
    """Get all defined plugins to health checks stated in plugins_list.

    Added filtration and removed sorting by identifier.

    """
    plugins = (
        plugin_class(**copy.deepcopy(options))
        for plugin_class, options in plugin_dir._registry
    )
    if plugins_list:
        plugins = filter(lambda x: x.identifier() in plugins_list, plugins)
    return tuple(plugins)


def run_plugin(plugin: AbstractHealthCheckBackend):
    """Run health check by using plugin.

    Moved outside of run_checks.

    """
    plugin.run_check()
    try:
        return plugin
    finally:
        from django.db import connections
        connections.close_all()


def run_checks(
    checks: Iterable[str] = None
) -> Tuple[AbstractHealthCheckBackend]:
    """Run health checks stated in checks(if empty run all them).

    Make it return plugins, instead of collected errors.

    """
    if not checks:
        checks = tuple()
    plugins = get_plugins(checks)

    with ThreadPoolExecutor(max_workers=len(plugins) or 1) as executor:
        for _ in executor.map(run_plugin, plugins):
            pass

    return plugins
