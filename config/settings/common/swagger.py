from libs.utils import get_latest_version

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        }
    },
}

API_INFO_BACKEND = {
    'title': 'JustLaw API',
    'default_version': get_latest_version(
        'changelog_backend/changelog.md'
    ),
    'description': 'JustLaw swagger API specification',
}
