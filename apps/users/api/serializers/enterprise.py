from rest_framework import serializers

from s3direct.api.fields import S3DirectUploadURLField

from ....core.api.serializers import BaseSerializer
from ....users import models
from .auth import AppUserRelatedRegisterSerializerMixin
from .enterprise_link import MemberSerializer
from .extra import FirmLocationSerializer, FirmSizeSerializer


class EnterpriseSerializer(BaseSerializer):
    """Serializer for Enterprise model."""
    firm_locations = FirmLocationSerializer(
        many=True, required=False
    )
    team_members = MemberSerializer(
        many=True, required=False
    )
    firm_size_data = FirmSizeSerializer(
        source='firm_size', read_only=True
    )
    team_logo = S3DirectUploadURLField(required=False, allow_null=True)

    class Meta:
        model = models.Enterprise
        fields = (
            'id',
            'team_logo',
            'is_verified',
            'verification_status',
            'followers',
            'featured',
            'role',
            'firm_name',
            'firm_size',
            'firm_size_data',
            'firm_locations',
            'team_members'
        )
        read_only_fields = (
            'user',
            'verification_status',
            'followers',
            'featured',
        )
        relations = (
            'user',
            'firm_locations',
            'team_members',
            'firm_size'
        )

    def to_representation(self, instance):
        if instance.team_logo == '[]':
            instance.team_logo = None
        data = super().to_representation(instance=instance)
        return data


class EnterpriseRegisterSerializer(
    AppUserRelatedRegisterSerializerMixin, EnterpriseSerializer
):
    """RegisterSerializer for Enterprise"""

    class Meta(EnterpriseSerializer.Meta):
        fields = EnterpriseSerializer.Meta.fields + (
            'password1',
            'password2'
        )
        relations = EnterpriseSerializer.Meta.relations + (
            'email',
            'avatar',
            'first_name',
            'middle_name',
            'last_name'
        )
        extra_kwargs = {
            'firm_name': {
                'required': False
            }
        }

    def validate(self, data):
        """Check registration data"""
        data = super().validate(data)
        return super(EnterpriseSerializer, self).validate(data)

    def create_related(self, user):
        """Save enterprise entry"""
        enterprise_data = self.validated_data.copy()
        enterprise_data['user'] = user
        models.Enterprise.objects.create(**enterprise_data)

    def create_entry(self, user):
        """Used for creating enterprise entry without creating user"""
        enterprise_data = self.validated_data.copy()
        for key in self.validated_data:
            if key not in ['role', 'firm_size']:
                del enterprise_data[key]
        enterprise_data['user'] = user
        models.Enterprise.objects.create(**enterprise_data)


class EnterpriseOnboardingSerializer(EnterpriseSerializer):
    """OnboardingSerializer for enterprise"""

    class Meta(EnterpriseSerializer.Meta):
        read_only_fields = EnterpriseSerializer.Meta.read_only_fields + \
                           ('role',)

    def validate(self, data):
        """Check registration data"""
        data = super().validate(data)
        if len(data.get('team_members')) > 20:
            raise serializers.ValidationError(
                "Exceed maximum number of team members"
            )
        return data

    def update(self, enterprise_id, validated_data):
        enterprise = models.Enterprise.objects.get(pk=enterprise_id)
        user = enterprise.user
        """Update attorney/paralegal model linked to enterprise admin"""
        if user.is_attorney:
            from apps.users.api.serializers import AttorneyOnboardingSerializer
            serializer = AttorneyOnboardingSerializer(
                data=self.context['request'].data
            )
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            attorney = serializer.update(user.pk, data)
            user = attorney.user
        elif user.is_paralegal:
            from apps.users.api.serializers import (
                ParalegalOnboardingSerializer,
            )
            serializer = ParalegalOnboardingSerializer(
                data=self.context['request'].data
            )
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            paralegal = serializer.update(user.pk, data)
            user = paralegal.user

        user.onboarding = True
        user.save()
        firm_locations = validated_data.pop(
            'firm_locations', []
        )
        team_members = validated_data.pop(
            'team_members', []
        )

        # Create firm locations
        for obj in enterprise.firm_locations.all():
            models.FirmLocation.objects.filter(id=obj.id).delete()
            enterprise.firm_locations.remove(obj)
        for obj in firm_locations:
            location = models.FirmLocation.objects.create(**obj)
            enterprise.firm_locations.add(location)

        # Create team members
        for obj in enterprise.team_members.all():
            models.Member.objects.filter(id=obj.id).delete()
            enterprise.team_members.remove(obj)
        for obj in team_members:
            member = models.Member.objects.create(**obj)
            member._send_invitation(enterprise)
            enterprise.team_members.add(member)
        super().update(enterprise, validated_data)
        return models.Enterprise.objects.get(pk=enterprise_id)


class EnterpriseAndAdminUserSerializer(
    EnterpriseSerializer
):
    """Serializer for enterprise and admin."""
    admin_user_data = serializers.SerializerMethodField(read_only=True)

    class Meta(EnterpriseSerializer.Meta):
        fields = EnterpriseSerializer.Meta.fields + ('admin_user_data',)

    def get_admin_user_data(self, obj):
        if obj.user.is_attorney:
            from apps.users.api.serializers import AttorneySerializer
            return AttorneySerializer(obj.user.attorney).data
        elif obj.user.is_paralegal:
            from apps.users.api.serializers import ParalegalSerializer
            return ParalegalSerializer(obj.user.paralegal).data
        return None


class UpdateEnterpriseSerializer(EnterpriseAndAdminUserSerializer):

    class Meta(EnterpriseAndAdminUserSerializer.Meta):
        read_only_fields = EnterpriseAndAdminUserSerializer.\
            Meta.read_only_fields + ('role', 'admin_user_data')

    def validate(self, data):
        """Check registration data"""
        data = super().validate(data)
        if len(data.get('team_members')) > 20:
            raise serializers.ValidationError(
                "Exceed maximum number of team members"
            )
        return data

    def update(self, enterprise, validated_data):
        user = enterprise.user
        """Update attorney/paralegal model linked to enterprise admin"""
        if user.is_attorney:
            from apps.users.api.serializers import UpdateAttorneySerializer
            serializer = UpdateAttorneySerializer(
                data=self.context['request'].data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            serializer.update(user.attorney, data)
        elif user.is_paralegal:
            from apps.users.api.serializers import UpdateParalegalSerializer
            serializer = UpdateParalegalSerializer(
                data=self.context['request'].data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            serializer.update(user.paralegal, data)

        firm_locations = validated_data.pop(
            'firm_locations', []
        )
        team_members = validated_data.pop(
            'team_members', []
        )
        # Update firm location
        for obj in enterprise.firm_locations.all():
            models.FirmLocation.objects.filter(id=obj.id).delete()
            enterprise.firm_locations.remove(obj)
        for obj in firm_locations:
            location = models.FirmLocation.objects.create(**obj)
            enterprise.firm_locations.add(location)

        # Update team member
        for obj in enterprise.team_members.all():
            models.Member.objects.filter(id=obj.id).delete()
            enterprise.team_members.remove(obj)
        for obj in team_members:
            member = models.Member.objects.create(**obj)
            member._send_invitation(enterprise)
            enterprise.team_members.add(member)
        super().update(enterprise, validated_data)
        return models.Enterprise.objects.get(pk=enterprise.pk)


class EnterpriseRegisterValidSerializer(serializers.Serializer):
    """Serializer to validate enterprise registration process"""
    stage = serializers.ChoiceField(choices=['first', 'second'], required=True)


class EnterpriseRegisterValidFirstStepSerializer(
    AppUserRelatedRegisterSerializerMixin
):
    """Simple serializer for enterprise 1st registration step validation."""
    username = serializers.ReadOnlyField()


class EnterpriseRegisterValidSecondStepSerializer(
    EnterpriseSerializer
):
    """Simple serializer for enterprise 2d registration step validation."""
    email = serializers.ReadOnlyField(source='user.email')

    def prepare_instance(self, attrs):
        """Overridden method to make `instance.clean_user()` method work.

        As far as this serializer is used for Enterprise registration
        validation on the 2d step, we don't have `user` instance for
        current Enterprise (cause we validate only 2d step fields and
        `email` is absent there).
        So `clean_user` instance check breaks in Enterprise model.

        To fix this there is set an empty `AppUser` instance to related
        serializer instance.

        """
        instance = super().prepare_instance(attrs)
        instance.user = models.AppUser()
        return instance
