import logging
import uuid
from typing import List, Sequence, Tuple, Union
from unittest import mock

from django.conf import settings

import firebase_admin
from firebase_admin import auth, firestore
from google.cloud.firestore_v1 import (
    Client,
    CollectionReference,
    DocumentReference,
    DocumentSnapshot,
)

from libs.testing.decorators import assert_not_testing

from apps.users.models import AppUser

__all__ = (
    'FirestoreClient',
    'FirestoreTestClient',
)

logger = logging.getLogger('firestore')


class FirestoreClient:
    """Google client to work with Firebase `firestore` service

    Tutorial with main principles of work with FireStore:
        https://firebase.google.com/docs/firestore/data-model

    """

    def __init__(self, *args, **kwargs):
        """Initialize Firestore client."""
        credentials = firebase_admin.credentials.Certificate(
            settings.FIREBASE_CONFIG
        )
        self.app: firebase_admin.App = firebase_admin.initialize_app(
            credentials,
            name=settings.FIREBASE['CLIENT_NAME']
        )
        self.client: Client = firestore.client(app=self.app)

    def document(self, path: str) -> DocumentReference:
        """Get document."""
        return self.client.document(path)

    def collection(self, *collection_path: str) -> CollectionReference:
        """Get collection."""
        return self.client.collection(*collection_path)

    @assert_not_testing
    def generate_token(self, user: AppUser):
        """Generate user token to access Firestore.

        Args:
            user (User): user which will access Firestore with generated JWT
                token

        Returns:
            (str): generated JWT token for a user to use Firestore

        """
        logger.debug(
            f'Firestore token created.\n'
            f'AppUser: {user.id}'
        )

        return auth.create_custom_token(
            uid=str(user.id),
            app=self.app
        )

    @assert_not_testing
    def create_or_update(self, path: str, data: dict = None):
        """Method to create/update a document in Firestore.

        If a document does not exist, creates the new one. If the document
        exists, rewrites it with the sent one.

        Args:
            path (str): path to the Firestore document.
            data (dict): object to store as a document in Firestore DB

        """
        self.document(path).set(data)

    @assert_not_testing
    def partial_update(self, path: str, data: dict):
        """Method to update a document`s fields in Firestore.

        Used to update some particular fields of the document.

        Args:
            path (str): path to the Firestore document.
            data (dict): object data to update Firestore document.

        """
        self.document(path).update(data)

    @assert_not_testing
    def delete(self, path: str):
        """Method to delete a document from Firestore.

        Completely remove the document from DB.

        Args:
            path (str): path to the Firestore document.

        """
        self.document(path).delete()

    @assert_not_testing
    def get(self, path: str) -> DocumentSnapshot:
        """Method to get a document from Firestore.

        Args:
            path (str): path to the Firestore document.

        Returns:
            (DocumentSnapshot): representation of Firestore document.

        """
        return self.document(path).get()

    @assert_not_testing
    def document_exists(self, path: str) -> bool:
        """Method to check existence of a document in Firestore.

        Existent Firestore document provides `create_time` value.

        Args:
            path (str): path to the Firestore document.

        Returns:
            (bool): if the document exists or not

        """
        return self.document(path).get().exists

    @assert_not_testing
    def list(
        self,
        path: str,
        *conditions: List[Tuple[str, str, Union[str, int, list]]]
    ) -> Sequence[DocumentSnapshot]:
        """Method to get a collection from Firestore.

        Args:
            path (str): path to the Firestore collection.
            conditions (list): list of conditions to perform queries. Each
                is a `tuple` with the following format:

                    (field (str), operation (str), value)

                Examples:
                    ('state', '==', 'CA')
                    ('state', 'in', ['CA', 'AC'])
                    ('population', '<', 1000000)

                For more details, see the docs:
                https://firebase.google.com/docs/firestore/query-data/queries

        Returns:
            collection (list): list of Firestore documents. Each is a
                `DocumentSnapshot`.

        """
        # Firestore returns collection as a generator of documents
        query = self.collection(path)
        for condition in conditions:
            query = query.where(*condition)
        documents = list(query.stream())
        return documents


class FirestoreTestClient(FirestoreClient):
    """Test client should be used for tests to avoid real API calls.

    Test methods simulate requests to Firestore.

    """

    def __init__(self, *args, **kwargs):
        pass

    def generate_token(self, user: AppUser):
        """Simulate generation of Firestore access token.

        Returns custom uuid instead of real API calls.

        """
        return str(uuid.uuid4())

    def _get_fake_object(self):
        """Return fake Firestore object.

        The fake object behaves like `google.cloud.DocumentSnapshot` object.

        """
        doc = mock.Mock()
        doc.id = mock.PropertyMock(return_value=str(uuid.uuid4()))
        doc.to_dict = mock.Mock(return_value={
            'id': 1,
            'participants': [1, 2],
        })
        return doc

    def create_or_update(self, path: str, data: dict):
        pass

    def partial_update(self, path: str, data: dict):
        pass

    def delete(self, path: str):
        pass

    def get(self, path: str):
        return self._get_fake_object()

    def document_exists(self, path: str):
        return True

    def list(
        self,
        path: str,
        conditions: List[Tuple[str, str, Union[str, int, list]]] = None
    ):
        return list()
