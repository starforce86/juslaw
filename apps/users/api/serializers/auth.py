from django.conf import settings
from django.contrib.auth import get_user_model, password_validation
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated, ValidationError

from allauth.account import app_settings
from allauth.account.forms import default_token_generator
from rest_auth import serializers as auth_serializers
from rest_auth.registration.serializers import RegisterSerializer
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from apps.users.models import AppUser

from ..serializers import auth_forms


class RemoveUsernameFieldMixin:
    """Removes username field."""

    def get_fields(self):
        """Remove 'username' from fields."""
        fields = super().get_fields()
        del fields['username']
        return fields


class AppUserLoginSerializer(
    RemoveUsernameFieldMixin,
    auth_serializers.LoginSerializer
):
    """LoginSerializer without username field."""
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        User = get_user_model()
        email = attrs.get('email')
        password = attrs.get('password')
        code = attrs.get('code')

        user = None

        if email and password:
            user = User.objects.filter(email__iexact=email).first()
        if user and not user.is_active:
            msg = 'This user\'s application is still pending'
            raise NotAuthenticated(msg)

        user = self._validate_email(email, password)

        if user is None:
            msg = _('Unable to log in with provided credentials.')
            raise ValidationError(msg)

        if 'rest_auth.registration' in settings.INSTALLED_APPS:
            if app_settings.EMAIL_VERIFICATION == \
                    app_settings.EmailVerificationMethod.MANDATORY:
                email_address = user.emailaddress_set.get(email=user.email)
                if not email_address.verified:
                    raise ValidationError(_('E-mail is not verified.'))

        if user.twofa and user.phone:
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            service = settings.TWILIO_SERVICE
            try:
                client = Client(account_sid, auth_token)

                verification_check = client.verify.services(service)\
                    .verification_checks.create(to=user.phone, code=code)
                if not verification_check.valid:
                    raise ValidationError(_('The code is incorrect'))
            except TwilioRestException:
                raise ValidationError(_('The code is incorrect'))

        attrs['user'] = user
        return attrs


class AppUserLoginValidationSerializer(
    RemoveUsernameFieldMixin,
    auth_serializers.LoginSerializer
):
    """LoginSerializer without username field."""
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        User = get_user_model()
        email = attrs.get('email')
        password = attrs.get('password')

        user = None

        if email and password:
            user = User.objects.filter(email__iexact=email).first()
        if user and not user.is_active:
            msg = 'This user\'s application is still pending'
            raise NotAuthenticated(msg)

        user = self._validate_email(email, password)

        attrs['user'] = user
        return attrs


class AppUserRelatedRegisterSerializerMixin(RegisterSerializer):
    """Serializer mixin for registration of attorney and client.

    This serializer mixin contains common fields and logic required for
    registration of attorney and client.

    """

    def get_cleaned_data(self):
        """Persist extra data during registration API call.

        Also clean validated_data from registration data(email and passwords).
        If you add extra data, don't forget to update AccountAdapter.
        """
        cleaned_data = super().get_cleaned_data()
        user_data = self.validated_data.pop('user', {})
        self.validated_data.pop('password1')
        self.validated_data.pop('password2')
        email = self.validated_data.pop('email')

        cleaned_data.update({
            'email': email,
            'first_name': user_data['first_name'],
            'middle_name': user_data.get('middle_name', None),
            'last_name': user_data['last_name'],
            'phone': user_data['phone'],
            'avatar': user_data.get('avatar', []),
            'specialities': user_data.get('specialities', []),
        })
        return cleaned_data

    def save(self, request):
        """Create related profile for new user and set specialities."""
        try:
            user = super().save(request)
        except IntegrityError:
            # This will happen when we try to register multiple users with
            # same email at the same time
            raise ValidationError(
                dict(
                    email=(
                        'A user is already registered with '
                        'this e-mail address.'
                    )
                )
            )
        user.specialities.set(self.cleaned_data['specialities'])
        self.create_related(user)
        return user

    def create_related(self, user):
        """Create related to user entry(Attorney or Client)."""
        raise NotImplementedError('Implement logic of creation!')


class AppUserPasswordResetSerializer(auth_serializers.PasswordResetSerializer):
    """View for password reset."""
    password_reset_form_class = auth_forms.ResetPasswordForm

    def validate_email(self, email):
        """Check that email assigned to user."""
        self.reset_form = self.password_reset_form_class(
            data=self.initial_data
        )
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(
                'The e-mail address is not assigned to any user account'
            )
        return email


class AppUserPasswordResetConfirmSerializer(
    auth_serializers.PasswordResetConfirmSerializer
):
    """Custom password reset confirm serializer."""

    TOKEN_ERROR_MESSAGE = 'Token is expired or incorrect. ' \
                          'Try resetting password once again.'

    def validate(self, attrs):
        """Validate user instance.

        This method is identical to original `validate` method but without
        `uid` format validation, because `User` model id is not an uuid.
        Also it uses all_auth default_token_generator, instead django's
        default one.

        """
        User = get_user_model()
        self._errors = {}

        try:
            # Removed uid format validation in this line
            self.user = User.objects.get(pk=attrs['uid'])
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError({'uid': [self.TOKEN_ERROR_MESSAGE]})

        self.custom_validation(attrs)
        # Construct SetPasswordForm instance
        self.set_password_form = self.set_password_form_class(
            user=self.user,
            data=attrs
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        # We use default_token_generator from all_auth package
        if not default_token_generator.check_token(
            self.user, attrs['token']
        ):
            raise ValidationError({'token': [self.TOKEN_ERROR_MESSAGE]})

        return attrs


class TokenSerializer(auth_serializers.TokenSerializer):
    """Overridden default token serializer.

    It has `user_type`, so that front-end team could understand who they are
    dealing with.

    """
    user_type = serializers.ChoiceField(
        source='user.user_type',
        choices=AppUser.USER_TYPES
    )

    avatar = serializers.CharField(
        source='user.avatar_url'
    )

    user_id = serializers.CharField(
        source='user.pk'
    )

    plan_id = serializers.CharField(
        source='user.plan_id'
    )

    phone = serializers.CharField(
        source='user.phone'
    )

    onboarding = serializers.BooleanField(
        source='user.onboarding'
    )

    class Meta(auth_serializers.TokenSerializer.Meta):
        fields = (
            'key',
            'user_type',
            'avatar',
            'user_id',
            'plan_id',
            'onboarding',
            'phone',
        )


class AppUserPasswordChangeSerializer(
    auth_serializers.PasswordChangeSerializer
):
    """Overridden to validate password1 before SetPasswordForm full_clean."""

    def validate_new_password1(self, password):
        """Validate new password."""
        password_validation.validate_password(password, self.user)
        return password
