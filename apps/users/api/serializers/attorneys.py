from django.contrib.auth import get_user_model

from rest_framework import serializers

from ....core.api.serializers import BaseSerializer
from ....finance.models import FinanceProfile, PlanProxy
from ....promotion.api.serializers import AttorneyEventSerializer
from ....users import models
from ....utils.s3_direct.fields import S3DirectUploadURLListField
from ...models import Invite
from .attorney_links import AttorneyEducationSerializer
from .auth import AppUserRelatedRegisterSerializerMixin
from .extra import (
    AppointmentTypeSerializer,
    CurrenciesSerializer,
    FeeKindSerializer,
    FirmLocationSerializer,
    JurisdictionsSerializer,
    LanguageSerializer,
    PaymentTypeSerializer,
    SpecialitySerializer,
)
from .user import AppUserRelatedSerializerMixin


class AttorneySerializer(AppUserRelatedSerializerMixin, BaseSerializer):
    """Serializer for Attorney model."""

    type = serializers.CharField(source='user.user_type', read_only=True)
    education = AttorneyEducationSerializer(many=True, allow_empty=False)
    distance = serializers.FloatField(
        default=None,
        source='distance.m',
        label='Distance to attorney in meters',
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

    appointment_type_data = AppointmentTypeSerializer(
        source='appointment_type', many=True, read_only=True
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

    class Meta:
        model = models.Attorney
        fields = (
            'id',
            'distance',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'phone',
            'type',
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
            'specialities_data',
            'speciality_time',
            'speciality_matters_count',
            'fee_rate',
            'fee_types',
            'extra_info',
            'charity_organizations',
            'fee_types_data',
            'keywords',
            'is_submittable_potential',
            'registration_attachments',
            'appointment_type',
            'payment_type',
            'spoken_language',
            'appointment_type_data',
            'payment_type_data',
            'spoken_language_data',
            'fee_currency',
            'fee_currency_data',
            'tax_rate',
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
            'appointment_type',
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

    def get_fields_to_hide(self, instance: models.Attorney) -> tuple:
        """Hide registration_attachments from other users."""
        fields_to_hide = super().get_fields_to_hide(instance)
        user = self.user
        if user and user.pk != instance.pk:
            return fields_to_hide + ('registration_attachments',)
        return fields_to_hide


class AttorneyDetailSerializer(AttorneySerializer):
    """Added 2FA property into AttorneySerializer"""

    twofa = serializers.BooleanField(source='user.twofa', required=False)
    subscribed = serializers.BooleanField(
        source='user.subscribed',
        read_only=True
    )

    expiration_date = serializers.DateTimeField(
        source='user.expiration_date',
        read_only=True
    )

    class Meta(AttorneySerializer.Meta):
        fields = AttorneySerializer.Meta.fields + (
            'twofa',
            'subscribed',
            'expiration_date'
        )


class AttorneyShortSerializer(AttorneySerializer):
    """Short version of AttorneySerializer."""

    class Meta:
        model = models.Attorney
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
        )


class AttorneyOverviewSerializer(AttorneySerializer):
    """Serializes the limited attorney details for matter overview"""

    class Meta:
        model = models.Attorney
        fields = (
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'phone',
            'avatar',
        )


class UpdateAttorneySerializer(AttorneyDetailSerializer):
    """Update Serializer for Attorney model."""
    email = serializers.EmailField(
        source='user.email', read_only=True
    )

    def update(self, attorney, validated_data):
        """Update attorney entry.

        First relations, user specified, and after that we update user
        and attorney fields.
        """

        if 'fee_types' in validated_data:
            fee_types = validated_data.pop('fee_types')
            attorney.fee_types.set(fee_types)

        if 'practice_jurisdictions' in validated_data:
            practice_jurisdictions = validated_data.pop(
                'practice_jurisdictions', []
            )
            self.update_practice_jurisdictions(
                attorney, practice_jurisdictions
            )

        if 'registration_attachments' in validated_data:
            registration_attachments = validated_data.pop(
                'registration_attachments', []
            )
            self.update_registration_attachments(
                attorney, registration_attachments
            )

        if 'education' in validated_data:
            education = validated_data.pop('education', [])
            self.update_education(attorney, education)

        if 'firm_locations' in validated_data:
            firm_locations = validated_data.pop('firm_locations', [])
            self.update_firm_locations(attorney, firm_locations)

        return super().update(attorney, validated_data)

    def update_practice_jurisdictions(self, attorney, practice_jurisdictions):
        for obj in attorney.practice_jurisdictions.all():
            models.Jurisdiction.objects.filter(id=obj.id).delete()
            attorney.practice_jurisdictions.remove(obj)
        for obj in practice_jurisdictions:
            jurisdiction = models.Jurisdiction.objects.create(**obj)
            attorney.practice_jurisdictions.add(jurisdiction)

    def update_firm_locations(self, attorney, firm_locations):
        for obj in attorney.firm_locations.all():
            models.FirmLocation.objects.filter(id=obj.id).delete()
            attorney.firm_locations.remove(obj)
        for obj in firm_locations:
            firm_location = models.FirmLocation.objects.create(**obj)
            attorney.firm_locations.add(firm_location)

    def update_education(self, attorney, educations):
        """Update attorney education using data from serializer."""
        for obj in attorney.education.all():
            models.AttorneyEducation.objects.filter(id=obj.id).delete()
        models.AttorneyEducation.objects.bulk_create(
            models.AttorneyEducation(attorney=attorney, **education_data)
            for education_data in educations
        )

    def update_registration_attachments(
        self, attorney, registration_attachments
    ):
        """Update registration_attachments using data from serializer."""
        current_attachments = attorney.registration_attachments.all()

        # Ids that came from requests
        input_files_urls = set(registration_attachments)

        # Ids of attorney's attachments
        existing_files_urls = set(current_attachments.values_list(
            'attachment', flat=True
        ))

        to_add = input_files_urls - existing_files_urls
        to_delete = existing_files_urls - input_files_urls

        current_attachments.filter(attachment__in=to_delete).delete()

        models.AttorneyRegistrationAttachment.objects.bulk_create(
            models.AttorneyRegistrationAttachment(
                attorney=attorney,
                attachment=file_url,
            )
            for file_url in to_add
        )


class AttorneyOnboardingSerializer(AttorneySerializer):
    """OnboardingSerializer for attorney"""

    def update(self, attorney_id, validated_data):
        attorney = models.Attorney.objects.get(pk=attorney_id)
        user = attorney.user
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
        appointment_type = validated_data.pop(
            'appointment_type', None
        )
        spoken_language = validated_data.pop(
            'spoken_language', None
        )

        if fee_types is not None:
            attorney.fee_types.set(fee_types)
        if payment_type is not None:
            attorney.payment_type.set(payment_type)
        if appointment_type is not None:
            attorney.appointment_type.set(appointment_type)
        if spoken_language is not None:
            attorney.spoken_language.set(spoken_language)
        if practice_jurisdictions is not None:
            for obj in attorney.practice_jurisdictions.all():
                models.Jurisdiction.objects.filter(id=obj.id).delete()
                attorney.practice_jurisdictions.remove(obj)
            for obj in practice_jurisdictions:
                jurisdiction = models.Jurisdiction.objects.create(
                    **obj
                )
                attorney.practice_jurisdictions.add(jurisdiction)

        # Create Firm Location profile
        for obj in attorney.firm_locations.all():
            models.FirmLocation.objects.filter(id=obj.id).delete()
            attorney.firm_locations.remove(obj)
        for obj in firm_locations:
            location = models.FirmLocation.objects.create(**obj)
            attorney.firm_locations.add(location)

        # Create AttorneyEducation entries
        if education is not None:
            for obj in attorney.education.all():
                models.AttorneyEducation.objects.filter(id=obj.id).delete()
            models.AttorneyEducation.objects.bulk_create(
                models.AttorneyEducation(attorney=attorney, **education_data)
                for education_data in education
            )
        # Add attachments
        models.AttorneyRegistrationAttachment.objects.bulk_create(
            models.AttorneyRegistrationAttachment(
                attorney=attorney, attachment=file_url
            )
            for file_url in registration_attachments
        )

        return super().update(attorney, validated_data)


class AttorneyRegisterSerializer(
    AppUserRelatedRegisterSerializerMixin, AttorneySerializer
):
    """RegisterSerializer for Attorney."""
    payment_method = serializers.CharField(required=False)
    plan = serializers.SlugRelatedField(
        queryset=PlanProxy.objects.filter(active=True),
        slug_field='id',
        required=False
    )
    education = AttorneyEducationSerializer(
        many=True, allow_empty=False, required=False)

    specialities = serializers.ManyRelatedField(
        source='user.specialities',
        child_relation=serializers.PrimaryKeyRelatedField(
            queryset=models.Speciality.objects.all()
        ),
        required=False
    )

    class Meta(AttorneySerializer.Meta):
        fields = AttorneySerializer.Meta.fields + (
            'password1',
            'password2',
            'payment_method',
            'plan'
        )
        relations = AttorneySerializer.Meta.relations + (
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
            'appointment_type': {
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
        return super(AttorneySerializer, self).validate(data)

    def create_related(self, user):
        """Save attorney entry.

        First we create attorney entry, then we link related models.

        """
        # Extract data that would be set after attorney creation
        attorney_data = self.validated_data.copy()
        fee_types = attorney_data.pop('fee_types', None)
        education = attorney_data.pop('education', None)
        practice_jurisdictions = attorney_data.pop(
            'practice_jurisdictions', []
        )
        firm_locations = attorney_data.pop(
            'firm_locations', []
        )
        registration_attachments = attorney_data.pop(
            'registration_attachments', []
        )
        # Remove fields related with payment information
        attorney_data.pop('payment_method', None)
        payment_type = attorney_data.pop('payment_type', None)
        plan = attorney_data.pop('plan', None)
        appointment_type = attorney_data.pop(
            'appointment_type', None
        )
        spoken_language = attorney_data.pop(
            'spoken_language', None
        )
        attorney_data['user'] = user

        # M2M fields need to be set after attorney creation
        attorney = models.Attorney.objects.create(**attorney_data)

        # Store payment data
        FinanceProfile.objects.create(
            user=attorney.user,
            initial_plan=plan,
        )
        if fee_types is not None:
            attorney.fee_types.set(fee_types)
        if payment_type is not None:
            attorney.payment_type.set(payment_type)
        if appointment_type is not None:
            attorney.appointment_type.set(appointment_type)
        if spoken_language is not None:
            attorney.spoken_language.set(spoken_language)
        if practice_jurisdictions is not None:
            for obj in practice_jurisdictions:
                jurisdiction = models.Jurisdiction.objects.create(**obj)
                attorney.practice_jurisdictions.add(jurisdiction)

        # Create Firm Location profile
        for obj in firm_locations:
            location = models.FirmLocation.objects.create(**obj)
            attorney.firm_locations.add(location)

        # Create AttorneyEducation entries
        if education is not None:
            models.AttorneyEducation.objects.bulk_create(
                models.AttorneyEducation(attorney=attorney, **education_data)
                for education_data in education
            )
        # Add attachments
        models.AttorneyRegistrationAttachment.objects.bulk_create(
            models.AttorneyRegistrationAttachment(
                attorney=attorney, attachment=file_url
            )
            for file_url in registration_attachments
        )


class AttorneyRegisterValidateSerializer(serializers.Serializer):
    """Serializer to validate Attorney registration process"""
    stage = serializers.ChoiceField(choices=['first', 'second'], required=True)


class AttorneyRegisterValidateFirstStepSerializer(
    AppUserRelatedRegisterSerializerMixin
):
    """Simple serializer for attorney 1st registration step validation."""
    username = serializers.ReadOnlyField()


class AttorneyRegisterValidateSecondStepSerializer(
    AttorneySerializer
):
    """Simple serializer for attorney 2d registration step validation."""
    email = serializers.ReadOnlyField(source='user.email')

    def prepare_instance(self, attrs):
        """Overridden method to make `instance.clean_user()` method work.

        As far as this serializer is used for Attorney registration validation
        on the 2d step, we don't have `user` instance for current Attorney
        (cause we validate only 2d step fields and `email` is absent there).
        So `clean_user` instance check breaks in Attorney model.

        To fix this there is set an empty `AppUser` instance to related
        serializer instance.

        """
        instance = super().prepare_instance(attrs)
        instance.user = models.AppUser()
        return instance


class IndustryContactSerializer(serializers.Serializer):
    """Serializes industry contacts of an attorney."""
    user_id = serializers.SerializerMethodField(read_only=True)
    name = serializers.CharField(source='full_name')
    firm = serializers.SerializerMethodField(read_only=True)
    type = serializers.CharField(source='user_type', read_only=True)
    phone = serializers.SerializerMethodField(read_only=True)
    pending = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField(read_only=True)
    avatar = serializers.FileField(read_only=True)

    def get_firm(self, obj):
        try:
            if isinstance(obj, Invite):
                return
            obj_type = getattr(obj, obj.user_type, None)
            return obj_type.firm_name if obj_type else None
        except Exception:
            return None

    def get_phone(self, obj):
        if isinstance(obj, Invite):
            return obj.phone
        obj_type = getattr(obj, obj.user_type, None)
        return obj_type.user.phone if obj_type else None

    def get_pending(self, obj):
        if isinstance(obj, Invite):
            return True
        return False

    def get_user_id(self, obj):
        if isinstance(obj, Invite):
            return obj.uuid
        elif isinstance(obj, get_user_model()):
            return obj.id
        else:
            return obj.user_id

    class Meta:
        fields = (
            'user_id',
            'name',
            'firm',
            'type',
            'phone',
            'email',
            'pending',
            'avatar'
        )


class PersonalDetailSerializer(IndustryContactSerializer):
    """Serializes personal details of an attorney industry contact"""
    practice_areas = SpecialitySerializer(
        source='specialities',
        many=True
    )
    languages = serializers.SerializerMethodField(read_only=True)

    def get_languages(self, obj):
        if obj.user_type == 'attorney':
            languages_query_set = obj.attorney.spoken_language.all()
        if obj.user_type == 'paralegal':
            languages_query_set = obj.paralegal.spoken_language.all()

        return LanguageSerializer(
            languages_query_set,
            many=True
        ).data

    class Meta:
        fields = (
            'id',
            'name',
            'firm',
            'type',
            'type',
            'phone',
            'email',
            'years_of_experience',
            'practice_areas',
            'languages',
        )


class IndustryContactAboutSerializer(IndustryContactSerializer):
    """Serializes about info of attorney industry contact."""
    jurisdictions = serializers.SerializerMethodField(
        read_only=True
    )
    education = serializers.SerializerMethodField(
        read_only=True
    )
    biography = serializers.SerializerMethodField(read_only=True)

    def get_biography(self, obj):
        return getattr(
            obj,
            'paralegal',
            getattr(
                obj,
                'attorney',
                None
            )
        ).biography

    def get_jurisdictions(self, obj):
        if obj.user_type == 'attorney':
            jurisdictions_qs = obj.attorney.practice_jurisdictions.all()
        if obj.user_type == 'paralegal':
            jurisdictions_qs = obj.paralegal.practice_jurisdictions.all()
        return JurisdictionsSerializer(
            jurisdictions_qs,
            many=True
        ).data

    def get_education(self, obj):
        if obj.user_type == 'attorney':
            return AttorneyEducationSerializer(
                obj.attorney.education,
                many=True
            ).data
        else:
            from apps.users.api.serializers import ParalegalEducationSerializer
            return ParalegalEducationSerializer(
                obj.paralegal.education,
                many=True
            ).data

    class Meta:
        fields = (
            'biography',
            'jurisdictions_and_registrations',
            'education'
        )


class IndustryContactParalegalDetails(serializers.Serializer):
    """Serializes paralegal details for paralegal industry contact."""
    personal_details = serializers.SerializerMethodField(read_only=True)
    about = serializers.SerializerMethodField(read_only=True)
    payment_methods = serializers.SerializerMethodField(read_only=True)
    fee_types = serializers.SerializerMethodField(read_only=True)
    firm_locations = serializers.SerializerMethodField(read_only=True)
    address = serializers.SerializerMethodField(read_only=True)

    def get_address(self, obj):
        """Return user's address"""
        user_obj = getattr(
            obj,
            'paralegal',
            getattr(
                obj,
                'attorney',
                None
            )
        )
        if user_obj:
            return [obj.address for obj in user_obj.firm_locations.all()]
        else:
            return None

    def get_firm_locations(self, obj):
        return FirmLocationSerializer(
            getattr(
                obj,
                'paralegal',
                getattr(
                    obj,
                    'attorney',
                    None
                )
            ).firm_locations.all(),
            many=True
        ).data

    def get_personal_details(self, obj):
        return PersonalDetailSerializer(obj).data

    def get_about(self, obj):
        return IndustryContactAboutSerializer(obj).data

    def get_payment_methods(self, obj):
        return PaymentTypeSerializer(
            getattr(
                obj,
                'paralegal',
                getattr(
                    obj,
                    'attorney',
                    None
                )
            ).payment_type.all(),
            many=True
        ).data

    def get_fee_types(self, obj):
        return FeeKindSerializer(
            getattr(
                obj,
                'paralegal',
                getattr(
                    obj,
                    'attorney',
                    None
                )
            ).fee_types.all(),
            many=True
        ).data

    class Meta:
        fields = (
            'personal_details',
            'about',
            'fee_types',
            'payment_methods',
            'firm_locations',
        )


class IndustryContactAttorneyDetails(IndustryContactParalegalDetails):
    """Serializes paralegal details for attorney industry contact."""
    events = AttorneyEventSerializer(read_only=True, many=True)

    class Meta:
        fields = (
            'personal_details',
            'about',
            'events',
            'fee_types',
            'payment_methods',
            'firm_locations'
        )
