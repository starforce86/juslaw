import logging
import time
from typing import List
from urllib.parse import quote, urlencode

from django.conf import settings

import docusign_esign as docusign
from docusign_esign import (
    Document,
    EnvelopeDefinition,
    EnvelopesApi,
    EventNotification,
    Recipients,
    ReturnUrlRequest,
    Signer,
)
from docusign_esign.client.api_exception import ApiException
from docusign_esign.client.auth.oauth import Account, OAuthToken, OAuthUserInfo

from . import exceptions
from .constants import DS_CONFIG, ENVELOPE_STATUS_CREATED, ENVELOPE_STATUS_SENT

__all__ = (
    'DocuSignClient',
)

logger = logging.getLogger('docusign')


class DocuSignImpersonalizedClientMixin:
    """Mixin with whole DocuSign impersonated authorization workflow.

    There should be a separate Client instance for each user.

    Mixin provides possibility to:

        1. Check if client already provided `consent` for JusLaw app to perform
        actions on behalf of a user (`is_consent_obtained`).

        2. Allow to set JWT token for API client to make impersonated
        requests to DocuSign.

    Docs:

        https://developers.docusign.com/esign-rest-api/guides/authentication/
        oauth2-jsonwebtoken

    Usage:

        client = DocuSignClient(user_id='...')

        # if client already has consent -> just get token for him
        if client.is_consent_obtained():
            client.set_jwt_token()
        else:
            link = client.get_consent_link()
            # redirect link in browser and get `code` from returned response
            code = link.redirect().get_code()  # pseudo code
            client.process_consent(code)
            client.set_jwt_token()

        # do some actions with DocuSign (send envelop and etc)
        ....

        # update token if it is needed
        client.update_token()

    """
    # DocuSign user GUID
    user_id = None
    # DocuSign user default account
    default_account = None
    # flag which identifies if token was already received
    token_received = False
    # timestamp in seconds when last received token will be expired
    token_expires_timestamp = 0

    def __init__(
        self, user_id: str = None, default_account: dict = None,
        *args, **kwargs
    ) -> None:
        """Initialize class attributes

        Attributes:
            user_id (str) - user GUID in DocuSign if it is known or None
            default_account (dict) - user default account data if it is known

        """
        self.user_id = user_id or self.user_id
        self.default_account = default_account or self.default_account

    def update_token(self):
        """Shortcut to update expired client token if it is needed."""
        is_expired = (
            self._get_current_timestamp() > self.token_expires_timestamp
        )
        if self.user_id and (not self.token_received or is_expired):
            self.set_jwt_token()

    def is_consent_obtained(self) -> bool:
        """Check if impersonalized user consent is already obtained.

        It can be identified that user already given his consent by trying to
        get and set his JWT token with existing user ID (GUID) to DocuSign
        client. If method gets `user_id` argument and succeeds with
        authorization -> user's consent exists and is valid. Otherwise we
        consider that user has no consent.

        After this method usage in case of absent `consent` it is strongly
        recommended to get obtaining consent link `get_consent_link`.

        Returns:
            (bool) - flag if user had already given his consent

        """
        if not self.user_id:
            return False

        try:
            self._get_jwt_token(log_error=False)
            return True
        except (ApiException, exceptions.GetJWTTokenException):
            return False

    def process_consent(self, code: str) -> str:
        """Method to process obtained consent and save related user data.

        Before calling this method we should get a user `consent` to
        impersonate app requests as his own ones through link get from
        `get_consent_link` method, after going by this link with browser there
        will be returned a special `code` which should be used in this method.

        Then this method will:

            1. Exchange `code` to user Access Token to get `user_id` from
            `get_user_info` method later.
            (https://developers.docusign.com/esign-rest-api/guides/
            authentication/oauth2-code-grant#step-2-obtain-the-access-token)

            2. Get user info and get `user_id` from returned data and remember
            `default_account` from user info.
            (https://developers.docusign.com/esign-rest-api/guides/
            authentication/oauth2-jsonwebtoken#step-4-retrieve-user-account-data)

        After using this method it is strongly recommended to call
        `set_jwt_token` to make impersonated requests from DocuSign client.

        Attributes:
            code (str) - code returned after following the link from
            `get_consent_link` in browser

        Returns:
            (str) - impersonated user GUID in DocuSign

        """
        assert code, '`code` must be set'
        token = self._exchange_code_to_access_token(code)
        user_data = self._get_user_info(token.access_token)
        self.user_id = user_data.sub
        self.default_account = self._get_default_account(user_data)
        return self.user_id

    def set_jwt_token(self, refresh_default_account=False) -> None:
        """Method to set DocuSign JWT token.

        Methods handles setting JWT token for impersonated DocuSign API
        requests.

        It gets DocuSign JWT token, sets it for current client, gets
        `default_account` from user_data if it is needed and updates token
        expiration info.

        Attributes:
            refresh_default_account (bool) - flag if user `default_account`
            should be refreshed

        """
        assert self.user_id, '`user_id` must be set'
        # get JWT token for impersonated requests
        jwt_token = self._get_jwt_token()
        # use custom access token setting cause suddenly DocuSign API SDK
        # doesn't add `Bearer` auth keyword, so all requests are failed (401)
        self._set_access_token(jwt_token)

        # remember user default account if needed
        if refresh_default_account or not self.default_account:
            user_data = self._get_user_info(jwt_token.access_token)
            self.default_account = self._get_default_account(user_data)
            # set default account base URI as base client api path
            self._set_base_uri()

        self._update_token_info()

    def get_consent_link(self, state: str = None) -> str:
        """Get DocuSign link to obtain user consent.

        When an application authenticates to perform actions on behalf of a
        user (impersonalized), that user will be asked to grant consent for
        the set of scopes (sets of permissions) that the application has
        requested, unless they have previously already granted that consent.

        When this link will be opened on frontend side:

            1. Performed redirect through this link to DocuSign and
            gets consent.

            2. After consent is get DocuSign makes redirect to backend
            `callback` with `code` and `state` params.

        Docs:

        https://developers.docusign.com/esign-rest-api/guides/authentication/
        obtaining-consent#individual-consent

        Attributes:
            state (str) - unique user identifier on backend to match returned
                after getting consent response

        Returns:
            (str) - link to DocuSign obtaining content page

        """
        args = {
            'response_type': 'code',
            'scope': 'signature impersonation',
            'client_id': self.integration_key,
            'redirect_uri': self.consent_redirect_url,
            'state': state
        }
        # docusign incorrectly works when `space` is replaced as `+` in a link
        # so here is `quote_via=quote`, where `space` is replaced with `%20`
        query_str = urlencode(args, quote_via=quote)
        return f'https://{self.oauth_host_name}/oauth/auth?{query_str}'

    def _set_access_token(self, token: OAuthToken) -> None:
        """Shortcut to override default `client.set_access_token` SDK method.

        Original SDK method sets malformed authorization token without `Bearer`
        keyword, which leads to 401 Unauthorized errors on DocuSign restapi
        requests.

        Attributes:
            token (OAuthToken) - JWT token object, which should be set as
            authorization

        """
        self.client.default_headers['Authorization'] = (
            f'Bearer {token.access_token}'
        )

    def _set_base_uri(self) -> None:
        """Shortcut to set default account base URI to client.

        Without this step all API requests will be not successful, so we need
        to define `base_path` and API `host` from `default_account` params.

        """
        if not self.default_account:
            return

        self.client.set_base_path(self.default_account.base_uri)
        self.client.host = f'{self.default_account.base_uri}/restapi'

    def _get_jwt_token(self, log_error: bool = True) -> OAuthToken:
        """Get JWT token for API client to make impersonalized API requests.

        Docs:

        https://developers.docusign.com/esign-rest-api/guides/authentication/
        oauth2-jsonwebtoken#step-2-create-a-jwt-token

        Arguments:
            log_error (bool) -
                Should client log errors in case of Exception(In some cases
                when caught error is expected, we want to log it as warning
                instead of error, so that sentry won't think of it as an
                issue.)

        Returns:
            (OAuthToken) - prepared JWT token for a user

        """
        try:
            jwt_token = self.client.request_jwt_user_token(
                client_id=self.integration_key,
                user_id=self.user_id,
                oauth_host_name=self.oauth_host_name,
                private_key_bytes=self.private_key,
                expires_in=self.token_expiration
            )
            return jwt_token
        except ApiException as e:
            error_msg = f"DocuSign couldn't get JWT token: {e}"
            if log_error:
                logger.error(error_msg)
            else:
                logger.warning(error_msg)
            raise exceptions.GetJWTTokenException

    def _exchange_code_to_access_token(self, code: str) -> OAuthToken:
        """Transform `code` to `access_token` for further user data getting.

        It is required in cases when we don't know DocuSign ID of impersonated
        user. So we need to get it from `_get_user_info` method later with
        received through this method `access_token`.

        Attributes:
            code (str) - code returned after following the link from
            `get_consent_link` in browser (needed only when `user_id` unknown)

        Returns:
            (OAuthToken) - access token to gather user info from DocuSign when
            `user_id` is unknown.

        """
        try:
            token = self.client.generate_access_token(
                client_id=self.integration_key,
                client_secret=self.secret_key,
                code=code,
            )
            return token
        except ApiException as e:
            logger.error(f"DocuSign couldn't get access token: {e}")
            raise exceptions.GetAccessTokenException

    def _get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Method to get user data from DocuSign after getting his consent.

        After getting user consent trough `get_consent_link` method, it is
        needed to get user GUID from his DocuSign data for following
        authorization process (`set_access_token`).

        To get user info and GUID:

            1. Obtain user Access Token
            (https://developers.docusign.com/esign-rest-api/guides/
            authentication/oauth2-code-grant#step-2-obtain-the-access-token)

            2. Get user info
            (https://developers.docusign.com/esign-rest-api/guides/
            authentication/oauth2-jsonwebtoken#step-4-retrieve-user-account-data)

        Attributes:
            access_token (str) - access token with which DocuSign returns user
            info.

        Returns:
            (OAuthUserInfo) - serialized user info

        As a user GUID (unique identifier in DocuSign) should be used `sub`
        field in returned data.

        """
        try:
            user_data = self.client.get_user_info(access_token)
        except ApiException as e:
            logger.error(f"DocuSign couldn't get user info: {e}")
            raise exceptions.GetUserDataException
        return user_data

    def _get_default_account(self, user_info: OAuthUserInfo) -> Account:
        """Shortcut to get user default account from all accounts.

        Attributes:
            user_info (OAuthUserInfo) - object with DocuSign user info

        Returns:
            (Account) - Account object with info about user default account

        """
        return next(filter(lambda x: x.is_default, user_info.accounts))

    def _update_token_info(self) -> None:
        """Shortcut to update token info.

        It adds a flag to the client that token was already received and
        recalculates its expiration time.

        """
        self.token_received = True
        self.token_expires_timestamp = (
            self._get_current_timestamp() + self.token_expiration
        )

    def _get_current_timestamp(self):
        """Shortcut to get current timestamp."""
        return int(round(time.time()))


class DocuSignClient(DocuSignImpersonalizedClientMixin):
    """Client to work with docuSign SDK.

    Provides all required for DocuSign workflow methods.

    DocuSign guides: https://developers.docusign.com/esign-rest-api/guides/

    """
    base_path = DS_CONFIG['BASE_PATH']
    oauth_host_name = DS_CONFIG['OAUTH_HOST_NAME']
    integration_key = DS_CONFIG['INTEGRATION_KEY']
    token_expiration = DS_CONFIG['TOKEN_EXPIRATION']
    secret_key = DS_CONFIG['SECRET_KEY']
    private_key = bytes(DS_CONFIG['PRIVATE_RSA_KEY'], 'utf-8')
    draft_envelope_email_subject = DS_CONFIG['DRAFT_ENVELOPE_EMAIL_SUBJECT']

    def __init__(self, *args, **kwargs):
        """Initialize DocuSign API client."""
        super().__init__(*args, **kwargs)
        self.client = docusign.ApiClient(
            base_path=self.base_path,
            oauth_host_name=self.oauth_host_name,
        )

    @property
    def envelope_status_webhook_url(self):
        """Shortcut to get `envelope_status_webhook_url`."""
        return f"{settings.BASE_URL}{DS_CONFIG['ENVELOPE_STATUS_WEBHOOK_URL']}"

    @property
    def consent_redirect_url(self):
        """Shortcut to get `consent_redirect_url`."""
        return f"{settings.BASE_URL}{DS_CONFIG['CONSENT_REDIRECT_URL']}"

    def create_envelope(
        self, documents: List[Document], recipients: List[Signer],
        email_subject: str = None, is_open: bool = True,
        event_notification: EventNotification = None
    ) -> dict:
        """Method to create an Envelope.

        This method allows to create `draft` Envelope or not:

            - draft - not ready for signing envelope would be created, which
            won't be sent to signers through emails, it will just wait until
            it will be edited and sent to signers from edit view.

            - not draft - create ready for signing envelope in DocuSign, which
            will be sent to signers through emails.

        Attributes:
            documents (Document) - list of Envelope documents for signing
            recipients (signer) - list of Envelope signers
            email_subject (str) - title of DocuSign email for signing documents
            is_open (bool) - flag if DocuSign Envelope should be draft or not
            event_notification (EventNotification) - Envelope webhook setting
                to perform its statuses updates

        Returns:
            (dict) - dict with info about created Envelope

        """
        if not self.is_consent_obtained():
            raise exceptions.UserHasNoConsentException

        # update token if it is expired
        self.update_token()

        try:
            envelope_definition = EnvelopeDefinition(
                email_subject=email_subject or self.draft_envelope_email_subject,  # noqa
                documents=documents,
                recipients=Recipients(signers=recipients),
                status=self._get_status(is_open),
                event_notification=event_notification
            )

            envelope_api = EnvelopesApi(self.client)
            results = envelope_api.create_envelope(
                account_id=self.default_account.account_id,
                envelope_definition=envelope_definition,
            )
            logger.debug(f'Created new Envelope: {results.envelope_id}')
        except ApiException as e:
            logger.error(f"DocuSign couldn't create envelope: {e}")
            raise exceptions.CreateEnvelopeException

        return results

    def update_envelope(self, envelope_id: str, **kwargs) -> dict:
        """Update existing envelope with new parameters.

        Attributes:
            envelope_id (str) - id of updated Envelope in DocuSign

        Returns:
            (dict) - dict with info about updated Envelope

        """
        if not self.is_consent_obtained():
            raise exceptions.UserHasNoConsentException

        # update token if it is expired
        self.update_token()

        try:
            envelope_api = EnvelopesApi(self.client)
            results = envelope_api.update(
                account_id=self.default_account.account_id,
                envelope_id=envelope_id,
                **kwargs
            )
            logger.debug(f'Updated envelope: {envelope_id}')
        except ApiException as e:
            logger.error(
                f"DocuSign couldn't update envelope {envelope_id}: {e}"
            )
            raise exceptions.UpdateEnvelopeException

        return results

    def get_envelope_edit_link(
        self, envelope_id: str, return_url: str = '', log_error: bool = True
    ) -> str:
        """Shortcut to get `edit` link for Envelope by its id.

        Method generates `edit` link to DocuSign for already existing Envelope
        and returns it. This link can be opened without authorization only
        once, so next time it will require user authorization all the time.

        Arguments:
            envelope_id (str) - DocuSign envelope id
            return_url (str) - url to which DocuSign should redirect user
               after envelope editing
            log_error (bool) -
                Should client log errors in case of Exception(In some cases
                when caught error is expected, we want to log it as warning
                instead of error, so that sentry won't think of it as an issue.

        Returns:
            (str) - generated link to Envelope edit in DocuSign

        """
        if not self.is_consent_obtained():
            raise exceptions.UserHasNoConsentException

        # update token if it is expired
        self.update_token()

        try:
            envelope_api = EnvelopesApi(self.client)
            # not allow to set None value to not raise BadRequest errors
            return_url = '' if not return_url else return_url
            edit_url = envelope_api.create_edit_view(
                account_id=self.default_account.account_id,
                envelope_id=envelope_id,
                return_url_request=ReturnUrlRequest(return_url)
            )
        except ApiException as e:
            error_msg = f"DocuSign couldn't create edit view for envelope: {e}"
            if log_error:
                logger.error(error_msg)
            else:
                logger.warning(error_msg)

            # if there is a `ENVELOPE_DOES_NOT_EXIST` code in error - raise
            # `NoEnvelopeExistsException`
            if 'ENVELOPE_DOES_NOT_EXIST' in str(e):
                raise exceptions.NoEnvelopeExistsException
            # otherwise raise `CreateEditEnvelopeViewException`
            raise exceptions.CreateEditEnvelopeViewException

        return edit_url.url

    def _get_status(self, is_open: bool = True) -> str:
        """Shortcut to get `status` for Envelope depending on `is_open` param.
        """
        return ENVELOPE_STATUS_CREATED if is_open else ENVELOPE_STATUS_SENT
