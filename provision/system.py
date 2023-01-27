##############################################################################
# System shortcuts
##############################################################################

__all__ = (
    'chown',
)


def chown(context):
    """Shortcut for owning apps dir by current user after some files were
    generated using docker-compose (migrations, new app, etc)
    """
    context.run('sudo chown ${USER}:${USER} -R apps')
