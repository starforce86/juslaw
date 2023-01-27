from rest_framework import serializers

from ....core.api.serializers import BaseSerializer
from ....finance.models import FinanceProfile, PlanProxy
from ....users import models
from ....utils.s3_direct.fields import S3DirectUploadURLListField
from .auth import AppUserRelatedRegisterSerializerMixin
from .extra import (
    CurrenciesSerializer,
    FeeKindSerializer,
    FirmLocationSerializer,
    JurisdictionsSerializer,
    LanguageSerializer,
    PaymentTypeSerializer,
)
from .paralegal_links import ParalegalEducationSerializer
from .user import AppUserRelatedSerializerMixin


class ParalegalSerializer(AppUserRelatedSerializerMixin, BaseSerializer):
    """Serializer for Paralegal model."""

    education = ParalegalEducationSerializer(many=True, allow_empty=False)
    distance = serializers.FloatField(
        default=None,
        source='distance.m',
        label='Distance to paralegal in meters',
        read_only=True
    )

    fee_types_data = FeeKindSerializer(
        source='fee_types', many=True, read_only=True
    )

    practice_jurisdictions = JurisdictionsSerializer(
        many=True, required=False
    )

    firm_locations = FirmLocationSerializer(
        many=True, required=False
    )
    payment_type_data = PaymentTypeSerializer(
        source='payment_type', many=True, read_only=True
    )
    spoken_language_data = LanguageSerializer(
        source='spoken_language', many=True, read_only=True
    )
    fee_currency_data = CurrenciesSerializer(
        source='fee_currency', read_only=True
    )
    is_verified = serializers.ReadOnlyField()
    has_active_subscription = serializers.ReadOnlyField(
        source='user.has_active_subscription'
    )
    registration_attachments = S3DirectUploadURLListField(
        attr_path='attachment',
        allow_empty=True,
        required=False,
    )
    type = serializers.CharField(source='user.user_type', read_only=True)
    twofa = serializers.BooleanField(source='user.twofa', required=False)

    class Meta:
        model = models.Paralegal
        fields = (
            'id',
            'distance',
            'first_name',
            'middle_name',
            'last_name',
            'role',
            'email',
            'phone',
            'type',
            'twofa',
            'avatar',
            'biography',
            'firm_name',
            'website',
            'firm_locations',
            'is_verified',
            'has_active_subscription',
            'verification_status',
            'featured',
            'sponsored',
            'sponsor_link',
            'followers',
            'education',
            'practice_jurisdictions',
            'practice_description',
            'years_of_experience',
            'have_speciality',
            'specialities',
            'speciality_time',
            'speciality_matters_count',
            'fee_rate',
            'fee_types',
            'extra_info',
            'charity_organizations',
            'specialities_data',
            'fee_types_data',
            'keywords',
            'registration_attachments',
            'payment_type',
            'spoken_language',
            'payment_type_data',
            'spoken_language_data',
            'fee_currency',
            'fee_currency_data'
        )
        read_only_fields = (
            'user',
            'verification_status',
            'featured',
            'sponsored',
            'sponsor_link',
            'followers',
        )
        relations = (
            'user',
            'education',
            'specialities',
            'fee_types',
            'firm_locations',
            'practice_jurisdictions',
            'registration_attachments',
            'payment_type',
            'spoken_language',
            'fee_currency'
        )
        extra_kwargs = {
            'years_of_experience': {
                'required': True
            },
            'keywords': {
                'child': serializers.CharField(),
                'allow_empty': True,
                'required': False,
            }
        }

    @property
    def errors(self):
        """Make `education` error as  error for one instance.

        Request from front-end team.

        """
        errors = super().errors
        return errors

    def get_fields_to_hide(self, instance: models.Paralegal) -> tuple:
        """Hide registration_attachments from other users."""
        fields_to_hide = super().get_fields_to_hide(instance)
        user = self.user
        if user and user.pk != instance.pk:
            return fields_to_hide + ('registration_attachments',)
        return fields_to_hide


class ParalegalShortSerializer(ParalegalSerializer):
    """Short version of ParalegalSerializer."""

    class Meta:
        model = models.Paralegal
        fields = (
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'phone',
            'avatar',
            'is_verified',
            'verification_status',
            'featured',
            'sponsored',
            'has_active_subscription',
            'specialities',
            'specialities_data',
        )


class UpdateParalegalSerializer(ParalegalSerializer):
    """Update Serializer for Paralegal model."""
    email = serializers.EmailField(
        source='user.email', read_only=True
    )

    education = ParalegalEducationSerializer(many=True)

    def update(self, paralegal, validated_data):
        """Update paralegal entry.

        First relations, user specified, and after that we update user
        and paralegal fields.
        """

        if 'fee_types' in validated_data:
            fee_types = validated_data.pop('fee_types')
            paralegal.fee_types.set(fee_types)

        if 'practice_jurisdictions' in validated_data:
            practice_jurisdictions = validated_data.pop(
                'practice_jurisdictions', []
            )
            self.update_practice_jurisdictions(
                paralegal, practice_jurisdictions
            )

        if 'registration_attachments' in validated_data:
            registration_attachments = validated_data.pop(
                'registration_attachments', []
            )
            self.update_registration_attachments(
                paralegal, registration_attachments
            )

        if 'education' in validated_data:
            education = validated_data.pop('education', [])
            self.update_education(paralegal, education)

        if 'firm_locations' in validated_data:
            firm_locations = validated_data.pop('firm_locations', [])
            self.update_firm_locations(paralegal, firm_locations)

        return super().update(paralegal, validated_data)

    def update_practice_jurisdictions(self, paralegal, practice_jurisdictions):
        for obj in paralegal.practice_jurisdictions.all():
            models.Jurisdiction.objects.filter(id=obj.id).delete()
            paralegal.practice_jurisdictions.remove(obj)
        for obj in practice_jurisdictions:
            jurisdiction = models.Jurisdiction.objects.create(**obj)
            paralegal.practice_jurisdictions.add(jurisdiction)

    def update_firm_locations(self, paralegal, firm_locations):
        for obj in paralegal.firm_locations.all():
            models.FirmLocation.objects.filter(id=obj.id).delete()
            paralegal.firm_locations.remove(obj)
        for obj in firm_locations:
            firm_location = models.FirmLocation.objects.create(**obj)
            paralegal.firm_locations.add(firm_location)

    def update_education(self, paralegal, educations):
        """Update paralegal education using data from serializer."""
        for obj in paralegal.education.all():
            models.ParalegalEducation.objects.filter(id=obj.id).delete()
        models.ParalegalEducation.objects.bulk_create(
            models.ParalegalEducation(paralegal=paralegal, **education_data)
            for education_data in educations
        )

    def update_registration_attachments(
        self, paralegal, registration_attachments
    ):
        """Update registration_attachments using data from serializer."""
        current_attachments = paralegal.registration_attachments.all()

        # Ids that came from requests
        input_files_urls = set(registration_attachments)

        # Ids of paralegal's attachments
        existing_files_urls = set(current_attachments.values_list(
            'attachment', flat=True
        ))

        to_add = input_files_urls - existing_files_urls
        to_delete = existing_files_urls - input_files_urls

        current_attachments.filter(attachment__in=to_delete).delete()

        models.ParalegalRegistrationAttachment.objects.bulk_create(
            models.ParalegalRegistrationAttachment(
                paralegal=paralegal,
                attachment=file_url,
            )
            for file_url in to_add
        )


class ParalegalOnboardingSerializer(ParalegalSerializer):
    """OnboardingSerializer for paralegal"""

    def update(self, paralegal_id, validated_data):
        paralegal = models.Paralegal.objects.get(pk=paralegal_id)
        user = paralegal.user
        user.onboarding = True
        user.save()
        fee_types = validated_data.pop('fee_types', None)
        education = validated_data.pop('education', None)
        practice_jurisdictions = validated_data.pop(
            'practice_jurisdictions', []
        )
        firm_locations = validated_data.pop(
            'firm_locations', []
        )
        registration_attachments = validated_data.pop(
            'registration_attachments', []
        )
        payment_type = validated_data.pop('payment_type', None)
        spoken_language = validated_data.pop(
            'spoken_language', None
        )

        if fee_types is not None:
            paralegal.fee_types.set(fee_types)
        if payment_type is not None:
            paralegal.payment_type.set(payment_type)
        if spoken_language is not None:
            paralegal.spoken_language.set(spoken_language)
        if practice_jurisdictions is not None:
            for obj in paralegal.practice_jurisdictions.all():
                models.Jurisdiction.objects.filter(id=obj.id).delete()
                paralegal.practice_jurisdictions.remove(obj)
            for obj in practice_jurisdictions:
                jurisdiction = models.Jurisdiction.objects.create(
                    **obj
                )
                paralegal.practice_jurisdictions.add(jurisdiction)

        # Create Firm Location profile
        for obj in paralegal.firm_locations.all():
            models.FirmLocation.objects.filter(id=obj.id).delete()
            paralegal.firm_locations.remove(obj)
        for obj in firm_locations:
            location = models.FirmLocation.objects.create(**obj)
            paralegal.firm_locations.add(location)

        # Create ParalegalEducation entries
        if education is not None:
            for obj in paralegal.education.all():
                models.ParalegalEducation.objects.filter(id=obj.id).delete()
            models.ParalegalEducation.objects.bulk_create(
                models.ParalegalEducation(
                    paralegal=paralegal,
                    **education_data
                )
                for education_data in education
            )
        # Add attachments
        models.ParalegalRegistrationAttachment.objects.bulk_create(
            models.ParalegalRegistrationAttachment(
                paralegal=paralegal, attachment=file_url
            )
            for file_url in registration_attachments
        )

        return super().update(paralegal, validated_data)


class ParalegalRegisterSerializer(
    AppUserRelatedRegisterSerializerMixin, ParalegalSerializer
):
    """RegisterSerializer for Parlegal."""
    payment_method = serializers.CharField(required=False)
    plan = serializers.SlugRelatedField(
        queryset=PlanProxy.objects.filter(active=True),
        slug_field='id',
        required=False
    )
    education = ParalegalEducationSerializer(
        many=True, allow_empty=False, required=False)

    specialities = serializers.ManyRelatedField(
        source='user.specialities',
        child_relation=serializers.PrimaryKeyRelatedField(
            queryset=models.Speciality.objects.all()
        ),
        required=False
    )
    practice_jurisdictions = JurisdictionsSerializer(
        many=True, required=False
    )

    class Meta(ParalegalSerializer.Meta):
        fields = ParalegalSerializer.Meta.fields + (
            'password1',
            'password2',
            'payment_method',
            'plan'
        )
        relations = ParalegalSerializer.Meta.relations + (
            'email',
            'avatar',
            'first_name',
            'last_name'
        )
        extra_kwargs = {
            'fee_rate': {
                'required': False
            },
            'fee_types': {
                'required': False
            },
            'avatar': {
                'required': False
            },
            'license_info': {
                'required': False
            },
            'years_of_experience': {
                'required': False
            },
            'payment_type': {
                'required': False
            },
            'spoken_language': {
                'required': False
            }
        }

    def validate(self, data):
        """Check registration data."""
        data = super().validate(data)
        return super(ParalegalSerializer, self).validate(data)

    def create_related(self, user):
        """Save paralegal entry.

        First we create paralegal entry, then we link related models.

        """
        # Extract data that would be set after paralegal creation
        paralegal_data = self.validated_data.copy()
        fee_types = paralegal_data.pop('fee_types', None)
        education = paralegal_data.pop('education', None)
        practice_jurisdictions = paralegal_data.pop(
            'practice_jurisdictions', []
        )
        firm_locations = paralegal_data.pop(
            'firm_locations', []
        )
        registration_attachments = paralegal_data.pop(
            'registration_attachments', []
        )
        # Remove fields related with payment information
        paralegal_data.pop('payment_method', None)
        payment_type = paralegal_data.pop('payment_type', None)
        plan = paralegal_data.pop('plan', None)
        spoken_language = paralegal_data.pop(
            'spoken_language', None
        )
        paralegal_data['user'] = user

        # M2M fields need to be set after paralegal creation
        paralegal = models.Paralegal.objects.create(**paralegal_data)

        # Store payment data
        FinanceProfile.objects.create(
            user=paralegal.user,
            initial_plan=plan,
        )
        if fee_types is not None:
            paralegal.fee_types.set(fee_types)
        if payment_type is not None:
            paralegal.payment_type.set(payment_type)
        if spoken_language is not None:
            paralegal.spoken_language.set(spoken_language)
        if practice_jurisdictions is not None:
            for obj in practice_jurisdictions:
                jurisdiction = models.Jurisdiction.objects.create(**obj)
                paralegal.practice_jurisdictions.add(jurisdiction)

        # Create Firm Location profile
        for obj in firm_locations:
            location = models.FirmLocation.objects.create(**obj)
            paralegal.firm_locations.add(location)

        # Create ParalegalEducation entries
        if education is not None:
            models.ParalegalEducation.objects.bulk_create(
                models.ParalegalEducation(
                    paralegal=paralegal, **education_data
                )
                for education_data in education
            )
        # Add attachments
        models.ParalegalRegistrationAttachment.objects.bulk_create(
            models.ParalegalRegistrationAttachment(
                paralegal=paralegal, attachment=file_url
            )
            for file_url in registration_attachments
        )


class ParalegalRegisterValidateSerializer(serializers.Serializer):
    """Serializer to validate Paralegal registration process"""
    stage = serializers.ChoiceField(choices=['first', 'second'], required=True)


class ParalegalRegisterValidateFirstStepSerializer(
    AppUserRelatedRegisterSerializerMixin
):
    """Simple serializer for paralegal 1st registration step validation."""
    username = serializers.ReadOnlyField()


class ParalegalRegisterValidateSecondStepSerializer(
    ParalegalSerializer
):
    """Simple serializer for paralegal 2d registration step validation."""
    email = serializers.ReadOnlyField(source='user.email')

    def prepare_instance(self, attrs):
        """Overridden method to make `instance.clean_user()` method work.

        As far as this serializer is used for Paralegal registration validation
        on the 2d step, we don't have `user` instance for current Paralegal
        (cause we validate only 2d step fields and `email` is absent there).
        So `clean_user` instance check breaks in Paralegal model.

        To fix this there is set an empty `AppUser` instance to related
        serializer instance.

        """
        instance = super().prepare_instance(attrs)
        instance.user = models.AppUser()
        return instance
