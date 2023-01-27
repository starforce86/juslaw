"""It is file with different helper methods for Vault credentials

Here should be placed different helpers and shortcuts for easier work with
Vault credentials and following usage in `invoke` commands.

Note: import django settings inside invoke functions otherwise, you won't be
able to init project for first time.

"""

import json
import os

import requests
from invoke import UnexpectedExit, task

from . import common
from .common import print_error, print_warn


@task
def init_settings_local(context):
    """Shortcut to set settings from vault."""
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'
    vault_credentials = get_vault_credentials_from_console(context)
    set_settings_from_vault(vault_credentials)


def get_vault_credentials_from_console(context):
    """Get user credentials from console to login to Vault using vault-cli."""
    from django.conf import settings

    try:
        token = context.run(
            'vault login -method=oidc -token-only',
            env={'VAULT_ADDR': settings.VAULT_DOMAIN},
            pty=False,
            hide='err'
        )
        # Get token from stdout
        token = token.stdout
    except UnexpectedExit as e:
        print_error(
            "Can't retrieve vault token using vault CLI.\n"
            "Ensure that it is installed: "
            "https://learn.hashicorp.com/vault/getting-started/install\n"
            f"Error: {e}"
        )
        raise e
    return {
        'token': token
    }


def set_settings_from_vault(vault_credentials):
    """Load settings from vault and set them in settings file."""
    from django.conf import settings

    project_name = settings.VAULT_STORAGE

    # Load credentials
    try:
        credentials = get_credentials_from_vault(
            **vault_credentials,
            project_name=project_name
        )
    except SystemExit:
        print_warn('Got an error fetching credentials from vault')
        return

    # Set common credentials for {env}.py file
    update_settings_with_credentials(
        credentials=credentials,
        settings_path='config/settings/local.py',
        template='config/settings/local.py.template'
    )
    # Create firestore credentials files
    create_firebase_credentials(credentials, with_project_settings=True)


def get_credentials_from_vault(token: str, project_name: str):
    """Get credentials from Vault.

    WEB UI: https://vault.saritasa.io/
    Token auth is used to access Vault.

    Args:
        token (str): Auth token.
        project_name (str): Project name in Vault.

    Returns:
        (dict): credentials from Vault.

    """

    from django.conf import settings

    # get credentials using Vault token
    response = requests.get(
        f'{settings.VAULT_API}/projects/{project_name}',
        headers={'X-Vault-Token': token}
    )
    credentials = response.json()
    if not response.status_code == 200:
        common.print_error(
            f'Error while retrieving credentials from Vault '
            f'\n({response.request.url})\n{credentials}'
        )
        exit(1)
    return credentials['data']


def update_settings_with_credentials(
    credentials: dict,
    settings_path: str,
    template=None
):
    """Create `settings` file from `template` file.

    Set credentials received from the Vault.

    Args:
        credentials (dict): Parsed JSON with credentials from Vault.
        settings_path (str):
            Name of file with settings, e.g. `local.py`. Stores credentials
            received from the Vault.
        template (str):
            Name of template file for settings, e.g. `local.py.local`.
            Doesn't store credentials, they are replaced by '%variable%`.
            If not passed, use `settings` file as template.

    """
    if template is None:
        template = settings_path

    with open(template, 'r') as f:
        data = f.read()

    for cred_key, cred_value in credentials.items():
        if isinstance(cred_value, dict):
            for key, value in cred_value.items():
                data = data.replace(f"%{key}%", str(value))
            continue
        if isinstance(cred_value, int) or cred_value in ['True', 'False']:
            data = data.replace(f"'%{cred_key}%'", str(cred_value))
            continue
        data = data.replace(f"%{cred_key}%", str(cred_value))

    with open(settings_path, 'w') as f:
        f.write(data)


def create_json_settings_file(credentials: dict, filename: str):
    """Create JSON file with settings from Vault.

    Args:
        credentials (dict): Credentials received from Vault.
        filename (str): Filename for settings file.

    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        f.write(json.dumps(credentials, indent=4))


def create_firebase_credentials(
    credentials, force_update=True, with_project_settings=False
):
    """Create files with Firebase credentials

    Script uploads Firebase related `service_account` and `project settings`
    from vault and places them in `config/google-credentials/` folder. It is
    needed for different `Firebase` clients interaction.

    """
    from django.conf import settings

    config = settings.FIREBASE_ENV_CONFIG

    # add firebase `service_account` credentials in a json file
    settings_file = config['service_account_file']
    if force_update or not os.path.isfile(settings_file):
        create_json_settings_file(credentials['FIREBASE'], settings_file)

    if not with_project_settings:
        return

    # add firebase `project settings` credentials in a json file for local env
    settings_file = config['project_settings_file']
    if force_update or not os.path.isfile(settings_file):
        create_json_settings_file(
            credentials['FIREBASE_PROJECT'], settings_file
        )
