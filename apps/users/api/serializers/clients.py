from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from libs.django_cities_light.api.serializers import (
    CityShortSerializer,
    CountrySerializer,
    RegionSerializer,
)

from apps.business.models import Lead
from apps.core.api.serializers import BaseSerializer
from apps.users.api.serializers.attorneys import AttorneySerializer
from apps.users.api.serializers.extra import TimezoneSerializer

from ... import models
from .auth import AppUserRelatedRegisterSerializerMixin
from .user import AppUserRelatedSerializerMixin


class ClientShortSerializer(AppUserRelatedSerializerMixin, BaseSerializer):
    country_data = CountrySerializer(source='country', read_only=True)
    state_data = RegionSerializer(source='state', read_only=True)
    city_data = CityShortSerializer(source='city', read_only=True)
    timezone_data = TimezoneSerializer(source='timezone', read_only=True)
    twofa = serializers.BooleanField(source='user.twofa', required=False)
    type = serializers.CharField(source='user.user_type', read_only=True)

    class Meta:
        model = models.Client
        fields = (
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'phone',
            'type',
            'twofa',
            'job',
            'avatar',
            'client_type',
            'organization_name',
            'note',
            'country',
            'country_data',
            'state',
            'state_data',
            'city',
            'city_data',
            'timezone',
            'timezone_data',
        )
        read_only_fields = (
            'user',
        )


class ClientSerializer(ClientShortSerializer):
    """Serializer for Client model."""
    specialities = serializers.ManyRelatedField(
        source='user.specialities',
        child_relation=serializers.PrimaryKeyRelatedField(
            queryset=models.Speciality.objects.all()
        ),
        required=False
    )
    matters_count = serializers.SerializerMethodField(read_only=True)
    type = serializers.SerializerMethodField(read_only=True)

    def get_matters_count(self, obj):
        return obj.matters.count()

    def get_type(self, obj):
        user = self.user
        if user and user.is_attorney:
            if obj.matters.filter(attorney=user.attorney).exists():
                return 'client'
            elif obj.leads.filter(
                attorney=user.attorney, status=Lead.STATUS_CONVERTED
            ).exists():
                return 'client'
            else:
                return 'lead'
        elif user and user.is_enterprise:
            if obj.matters.filter(enterprise=user.enterprise).exists():
                return 'client'
            else:
                return 'lead'
        return None

    class Meta(ClientShortSerializer.Meta):
        model = models.Client
        fields = ClientShortSerializer.Meta.fields + (
            'help_description',
            'specialities',
            'zip_code',
            'address1',
            'address2',
            'matters_count',
            'twofa',
            'type'
        )
        relations = (
            'user',
            'specialities',
        )

    def get_fields_to_hide(self, instance: models.Client) -> tuple:
        """Hide client's email from other clients."""
        fields_to_hide = super().get_fields_to_hide(instance)
        user = self.user
        if user and user.is_client and user.pk != instance.pk:
            return fields_to_hide + ('email',)
        return fields_to_hide


class UpdateClientSerializer(ClientSerializer):
    """Update serializer for Client model."""
    email = serializers.EmailField(
        source='user.email', read_only=True
    )
    client_type = serializers.CharField(required=False)

    class Meta(ClientSerializer.Meta):
        fields = ClientSerializer.Meta.fields + (
            'client_type',
        )

    def validate(self, attrs):
        client_type = attrs.get('client_type', None)
        if client_type and client_type != 'client' and client_type != 'lead' \
                and client_type != 'firm' and client_type != 'individual':
            raise ValidationError('Invalid choice for client type')
        client = self.get_instance()
        if client_type == 'client' or client_type == 'lead':
            user = self.context.get('request').user
            if not user.is_attorney:
                return super().validate(attrs)
            attorney = user.attorney
            if client.matters.filter(attorney=attorney).count() \
                    and client_type == 'lead':
                raise ValidationError('Can not be lead')
            elif client.leads.filter(status='converted').count() \
                    and client_type == 'lead':
                raise ValidationError('Can not be lead')
        return super().validate(attrs)

    def update(self, instance, validated_data):
        obj = super().update(instance, validated_data)
        if validated_data.get('client_type', None) == 'individual':
            obj.organization_name = None
            obj.job = None
        if validated_data.get('client_type', None) is not None and \
                validated_data['client_type'] == 'client' and \
                obj.leads.filter(status='active').count():
            obj.leads.filter(status='active').update(status='converted')
        return obj


class ClientRegisterSerializer(
    AppUserRelatedRegisterSerializerMixin, ClientSerializer
):
    """RegisterSerializer for Client."""

    class Meta(ClientSerializer.Meta):
        fields = ClientSerializer.Meta.fields + (
            'password1',
            'password2',
        )
        relations = (
            'user',
            'email',
            'avatar',
            'first_name',
            'last_name'
        )

    def validate(self, data):
        """Check registration data."""
        data = super().validate(data)
        return super(ClientSerializer, self).validate(data)

    def create_related(self, user):
        """Save client entry."""
        client_data = self.validated_data.copy()
        client_data['user'] = user
        models.Client.objects.create(**client_data)


class ClientFavoriteAttorneySerializer(BaseSerializer):
    favorite_attorneys_data = AttorneySerializer(
        source='favorite_attorneys',
        many=True,
        read_only=True
    )

    class Meta:
        model = models.Client
        fields = (
            'favorite_attorneys',
            'favorite_attorneys_data'
        )
        relations = (
            'favorite_attorneys'
        )


class ClientInfoSerializer(AppUserRelatedSerializerMixin, BaseSerializer):

    class Meta:
        model = models.Client
        fields = (
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'avatar',
        )


class ClientDetailInfoSerializer(ClientInfoSerializer):
    country_data = CountrySerializer(source='country', read_only=True)
    state_data = RegionSerializer(source='state', read_only=True)
    city_data = CityShortSerializer(source='city', read_only=True)

    class Meta(ClientInfoSerializer.Meta):
        fields = ClientInfoSerializer.Meta.fields + (
            'phone',
            'country_data',
            'state_data',
            'city_data',
            'address1',
            'address2',
            'zip_code'
        )
