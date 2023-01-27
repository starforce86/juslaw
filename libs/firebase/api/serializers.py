from rest_framework import serializers


class FirestoreCredentialsSerializer(serializers.Serializer):
    """Simple serializer for Firestore credentials"""
    token = serializers.ReadOnlyField()
