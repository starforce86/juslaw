from .installed_apps import LOCAL_APPS


def show_toolbar_callback(request):
    """Do not show debug bar on this paths."""
    return not request.path.startswith('/pages')


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar_callback
}

# shell_plus configuration
# you can specify what additional libraries and blocks of
# code to be automatically imported when you run shell_plus
# command, in our case `inv shell`
# if you want factories to be included into your shell then you can do
# something like this
# *[('{}.factories'.format(app), '*')
#   for app in LOCAL_APPS + TESTING_APPS]
# right inside SHELL_PLUS_PRE_IMPORTS

# what packages to preload inside shell plus
TOOLS_FOR_SHELL = [
    'stripe',
    'arrow',
    ('itertools', '*'),
    ('collections', '*'),
    ('datetime', '*')
]
FACTORIES_FOR_SHELL = [
    (f'{app}.factories', '*')
    for app in LOCAL_APPS
    # django-extensions' shell from version 3.0 fails to start if it
    # fails to make pre imports
    if app not in (
        'libs',
        'apps.admin',
        'apps.accounting',
    )
]
SERVICES_FOR_SHELL = [
    (f'{app}.services', '*')
    for app in LOCAL_APPS
    if app not in (
        'libs',
        'apps.promotion',
        'apps.news',
    )
]
SHELL_PLUS_PRE_IMPORTS = (
    TOOLS_FOR_SHELL +
    FACTORIES_FOR_SHELL +
    SERVICES_FOR_SHELL
)

# Print SQL Queries
SHELL_PLUS_PRINT_SQL = False

# Truncate sql queries to this number of characters (this is the default)
SHELL_PLUS_PRINT_SQL_TRUNCATE = 1000
