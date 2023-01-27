from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from libs.firebase import default_firestore_client as firestore

from . import serializers


class FirestoreCredentialsView(GenericViewSet):
    """API View to get Firestore credentials."""
    pagination_class = None
    permission_classes = IsAuthenticated,
    serializer_class = serializers.FirestoreCredentialsSerializer

    @action(methods=['GET'], detail=False, url_path='get-credentials')
    def get(self, *args, **kwargs):
        """API method to get Firestore token for frontend team.

        With this token frontend team can work with firebase sdk and create
        corresponding chats and etc.

        """
        user_token = firestore.generate_token(self.request.user)
        serializer = self.get_serializer({'token': user_token})
        return Response(data=serializer.data, status=status.HTTP_200_OK)
