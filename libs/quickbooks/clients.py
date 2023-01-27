import logging
import uuid
from functools import wraps
from typing import Iterable, List, Tuple
from unittest.mock import MagicMock

from django.conf import settings

import arrow
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from intuitlib.exceptions import AuthClientError
from quickbooks import QuickBooks
from quickbooks import objects as qb_objects
from quickbooks.batch import batch_create
from quickbooks.exceptions import (
    AuthorizationException,
    ObjectNotFoundException,
    QuickbooksException,
)
from quickbooks.objects.batchrequest import BatchResponse

from libs.testing.decorators import assert_not_testing

from . import exceptions
from .services import create_qb_object

__all__ = (
    'QuickBooksClient',
    'QuickBooksTestClient',
)


logger = logging.getLogger('quickbooks')
QB_CONFIG = settings.QUICKBOOKS


def auth_required(method):
    """Decorator for QuickBookClient that keeps track of tokens."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Check that tokens exists and are not expired and refresh if possible
        """
        # check if `access_token` and `refresh_token` and `realm_id` defined
        client = self.auth_client
        if not all([client.access_token, client.refresh_token, client.realm_id]):  # noqa
            raise exceptions.NotAuthorized

        if self.is_refresh_token_expired:
            raise exceptions.RefreshTokenExpired

        if self.is_access_token_expired:
            self.refresh_tokens()
        try:
            return method(self, *args, **kwargs)

        except (AuthorizationException, AuthClientError) as error:
            error_msg = f'Authorization error: {error}'
            logger.warning(error_msg)
            raise exceptions.AuthError(error_msg)

    return wrapper


class QuickBooksClient:
    """Client used to authenticate and interact with QuickBook API.

    This client uses 2 different python packages to perform work with QB API:

        - intuitlib - common authorization client for Intuit apps
        - quickbooks - package to interact with QB API(CRUD operations and etc)

    """

    # level of access which QB user gives to app
    scopes = [Scopes.ACCOUNTING]

    def __init__(
        self,
        state_token: str = None,
        access_token: str = None,
        refresh_token: str = None,
        id_token: str = None,
        realm_id: str = None,
        expires_in: int = None,
        x_refresh_token_expires_in: int = None,
        user=None
    ):
        """Init QuickBook Client.

        To init QB Client, we need to make `auth` client and `api` client
        initialization and remember tokens expiration info.

        Attributes:
            state_token (str) - unique user identifier on backend to match
                returned after getting consent response
            access_token (str) - main user authorization token if he already
                logged in (expires in 60 minutes)
            refresh_token (str) - user refresh token with which expired
                authorization token may be updated (expires in 100 days)
            id_token (str) - ID Token for OpenID flow
            realm_id (str) - QBO Realm/Company ID
            expires_in (int) - timestamp when `access_token` expires
            x_refresh_token_expires_in (int) - timestamp when `refresh_token`
            expires user - some app user under which QB requests are made

        """
        self.auth_client = AuthClient(
            client_id=QB_CONFIG['CLIENT_ID'],
            client_secret=QB_CONFIG['CLIENT_SECRET'],
            redirect_uri=f'{settings.BASE_URL}/{QB_CONFIG["AUTH_REDIRECT_URL"]}',  # noqa
            environment=QB_CONFIG['ENVIRONMENT'],
            state_token=state_token,
            access_token=access_token,
            refresh_token=refresh_token,
            id_token=id_token,
            realm_id=realm_id,
        )
        self.user = user
        self.access_expires_in = expires_in
        self.refresh_expires_in = x_refresh_token_expires_in  # noqa

        self.api_client = None
        # We can init quickbook_api_client only if we have refresh token
        if self.refresh_token and self.realm_id:
            self._init_api_client()

    def _init_api_client(self):
        """Initiate client for interaction with api."""
        self.api_client = QuickBooks(
            auth_client=self.auth_client,
            refresh_token=self.refresh_token,
            company_id=self.realm_id,
        )

    @property
    def realm_id(self):
        return self.auth_client.realm_id

    @property
    def access_token(self):
        return self.auth_client.access_token

    @property
    def refresh_token(self):
        return self.auth_client.refresh_token

    @property
    def id_token(self):
        return self.auth_client.id_token

    @property
    def is_access_token_expired(self) -> bool:
        """Check if access token is expired."""
        return self._is_token_expired(self.access_expires_in)

    @property
    def is_refresh_token_expired(self) -> bool:
        """Check if refresh token if is expired."""
        return self._is_token_expired(self.refresh_expires_in)

    @assert_not_testing
    def get_authorization_url(self, state_token=None) -> str:
        """Generate auth url, where user is redirected to.

        User will be redirected to QuickBooks login page, where he will be
        asked to provide access to the app. In case of successful response
        user will be redirected to backend `AUTH_REDIRECT_URL` with
        `access_code`. Then backend will be responsible for exchanging
        `access_code` to `access_token` and `refresh_token` with usage of
        `get_bearer_token` method.

        Attributes:
            state_token (str) - unique user identifier on backend to match
                returned after getting consent response

        """
        return self.auth_client.get_authorization_url(
            scopes=self.scopes, state_token=state_token
        )

    @assert_not_testing
    def get_bearer_token(self, auth_code: str, realm_id=None) -> dict:
        """Get access_token and refresh_token using authorization code.

        This method completes authorization process for a user and exchanges
        `access_code` to access and refresh tokens with info about their
        expiration.

        Attributes:
            auth_code (str) - access code taken from QB auth url redirecting
            realm_id (str) - id of company/realm in QB

        """
        try:
            self.auth_client.get_bearer_token(
                auth_code=auth_code, realm_id=realm_id
            )
        except AuthClientError as e:
            # Just printing status_code here but it can be used for retry
            # workflow, etc
            logger.error(f'{e.status_code} {e.intuit_tid} {e.content}')
            raise e
        access_expires_in, refresh_expires_in = self._get_expiration_timestamps()  # noqa
        return {
            'realm_id': self.realm_id,
            'access_token': self.access_token,
            'expires_in': access_expires_in,
            'refresh_token': self.refresh_token,
            'x_refresh_token_expires_in': refresh_expires_in,
            'id_token': self.id_token,
        }

    @assert_not_testing
    def refresh_tokens(self):
        """Refresh access tokens and initialize API client with new tokens."""
        self.auth_client.refresh()
        self._init_api_client()
        self.access_expires_in, self.refresh_expires_in = \
            self._get_expiration_timestamps()

    @assert_not_testing
    def get_customers(self, limit: int = None) -> List[qb_objects.Customer]:
        """Load customers from API."""
        return self._get_objects(qb_objects.Customer, limit)

    @assert_not_testing
    def get_customer(self, customer_id: int) -> qb_objects.Customer:
        """Get `customer` by id from API."""
        return self._get_object(qb_objects.Customer, customer_id)

    @assert_not_testing
    def get_invoice(self, invoice_id: int) -> qb_objects.Invoice:
        """Get `invoice` by id from API."""
        return self._get_object(qb_objects.Invoice, invoice_id)

    @assert_not_testing
    @auth_required
    def save_object(self, qb_object):
        """Shortcut to save QB object in QuickBooks."""
        try:
            return qb_object.save(qb=self.api_client)
        except QuickbooksException as e:
            # duplicate errors have its separate codes
            if e.error_code == 6240:
                raise exceptions.DuplicatedObjectError(
                    f"The {qb_object.qbo_object_name} already exists: {e}"
                )
            raise exceptions.SaveObjectError(
                f"Can't save {qb_object.qbo_object_name}: {e}"
            )

    @assert_not_testing
    @auth_required
    def batch_create(self, objects: Iterable) -> BatchResponse:
        """Make a request to batch create list of objects.

        Returns batch response, which has:
            batch_responses: list of responses from API
            original_list: list of ordinal qb_objects
            successes: list of qb_objects, that were saved
            faults: list of qb_objects, that weren't saved

        """
        return batch_create(objects, qb=self.api_client)

    def _is_token_expired(self, expires_in: int) -> bool:
        """Shortcut to check whether token is expired."""
        if not expires_in:
            return True
        return arrow.utcnow() > arrow.get(expires_in)

    def _get_expiration_timestamps(self) -> Tuple[int, int]:
        """Shortcut to convert `expiration` to timestamps started from now.

        QuickBooks returns expiration for tokens as a simple amount of seconds,
        which means how long token would be valid. To perform `is_expired`
        check we need to compare current time with the time when token will
        become invalid calculated from `now`.

        """
        now = arrow.utcnow().timestamp
        access_expires_in = now + self.auth_client.expires_in
        refresh_expires_in = now + self.auth_client.x_refresh_token_expires_in
        return access_expires_in, refresh_expires_in

    @assert_not_testing
    @auth_required
    def _get_objects(self, qb_class, limit: int = 1000) -> List:
        """Load qb objects for QuickBook API.

        Arguments:
            qb_class: QB class of objects to be loaded
            limit (int):
                Limit of how much objects should be loaded, if limit is None
                then we make the amount of items in QuickBook db a limit, in
                other words we load all.

        """
        count = qb_class.count(qb=self.api_client)
        limit, offset = limit or 1000, 1
        objects = []
        while len(objects) != count:
            results = qb_class.all(
                qb=self.api_client, start_position=offset, max_results=limit
            )
            offset = offset + len(results)
            objects.extend(results)
        return objects

    @assert_not_testing
    @auth_required
    def _get_object(self, qb_class, object_id: int):
        """Shortcut to get QB object in QuickBooks."""
        try:
            return qb_class.get(id=object_id, qb=self.api_client)
        except ObjectNotFoundException:
            raise exceptions.ObjectNotFound(
                f'{qb_class.qbo_object_name} not found in QuickBooks'
            )


class QuickBooksTestClient(QuickBooksClient):
    """Separate test client for QuickBooks to avoid real API calls."""

    auth_client_mock = MagicMock(
        realm_id=str(uuid.uuid4()),
        access_token=str(uuid.uuid4()),
        refresh_token=str(uuid.uuid4()),
        id_token=str(uuid.uuid4()),
        state_token=str(uuid.uuid4()),
        expires_in=arrow.utcnow().timestamp() + 3600,
        x_refresh_token_expires_in=arrow.utcnow().timestamp() + 3600,
    )

    api_client_mock = MagicMock(
        auth_client=auth_client_mock,
        refresh_token=auth_client_mock.refresh_token,
        company_id=auth_client_mock.realm_id,
    )

    def __init__(self, *args, **kwargs):
        """Overridden client initialization to mock real API calls."""
        # special method which can be mocked in tests to set correct
        # `auth_client`
        self.auth_client = self._get_auth_client(*args, **kwargs)
        self.user = kwargs.get('user')
        self.access_expires_in = self.auth_client.expires_in
        self.refresh_expires_in = self.auth_client.x_refresh_token_expires_in
        self.api_client = None
        # We can init quickbook_api_client only if we have refresh token
        if self.refresh_token and self.realm_id:
            self._init_api_client()

    def _init_api_client(self):
        """Overridden client initialization to mock real API calls."""
        self.api_client = self.api_client_mock

    def _get_auth_client(self, *args, **kwargs):
        """Special method, which can be mocked in tests to set different auth.
        """
        return self.auth_client_mock

    def get_authorization_url(self, state_token=None) -> str:
        """Overridden method to mock real API calls."""
        return 'https://fake-url.com'

    def get_bearer_token(self, auth_code: str, realm_id=None) -> dict:
        """Overridden method to mock real API calls."""
        return {
            'realm_id': self.realm_id,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'id_token': self.id_token,
        }

    @auth_required
    def get_customers(self, limit: int = None) -> List[qb_objects.Customer]:
        """Overridden method to mock real API calls."""
        customer = self.get_customer(1)
        return [customer]

    @auth_required
    def get_customer(self, customer_id: int) -> qb_objects.Customer:
        """Overridden method to mock real API calls."""
        return self._get_object(qb_objects.Customer, 1)

    @auth_required
    def get_invoice(self, invoice_id: int) -> qb_objects.Invoice:
        """Overridden method to mock real API calls."""
        return self._get_object(qb_objects.Invoice, 1)

    @auth_required
    def save_object(self, qb_object):
        """Overridden method to mock real API calls."""
        return qb_object

    @auth_required
    def _get_object(self, qb_class, object_id: int):
        """Shortcut to get QB object in QuickBooks."""
        try:
            return self._qb_class_get(qb_class)
        except ObjectNotFoundException:
            raise exceptions.ObjectNotFound(
                f'{qb_class.qbo_object_name} not found in QuickBooks'
            )

    def _qb_class_get(self, qb_class):
        """Special method can be mocked for different `qb_class.get` behavior.
        """
        if qb_class == qb_objects.Invoice:
            return create_qb_object(
                qb_objects.Invoice,
                Id=1,
                SyncToken=0
            )

        if qb_class == qb_objects.Customer:
            return create_qb_object(
                qb_objects.Customer,
                Id=1,
                DisplayName="Amy's Bird Sanctuary",
                GivenName='Amy',
                FamilyName='Lauterbach',
                PrimaryEmailAddr=create_qb_object(
                    qb_objects.EmailAddress,
                    Address='Birds@Intuit.com'
                ),
                CompanyName="Amy's Bird Sanctuary"
            )
