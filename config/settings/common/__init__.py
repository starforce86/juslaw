# -----------------------------------------------------------------------------
# General Django Configuration Starts Here
# -----------------------------------------------------------------------------

from .admin import *
from .allauth import *
from .authentication import *
from .business_logic import *
from .cacheops import *
from .celery import *
from .cities import *
from .ckeditor import *
from .constance import *
from .cors import *
from .databases import *
from .dev_tools import *
from .docusign import *
from .drf import *
from .firebase import *
from .general import *
from .gis import *
from .health_check import *
from .imagekit import *
from .installed_apps import *
from .internationalization import *
from .logging import *
from .middleware import *
from .notifications import *
from .paths import *
from .quickbooks import *
from .s3 import *
from .security import *
from .sentry import *
from .static import *
from .storage import *
from .stripe import *
from .swagger import *
from .templates import *
from .vault import *

SITE_ID = 1
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TESTING = os.environ.get('PYTEST_TESTING', False)
