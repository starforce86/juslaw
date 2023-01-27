from django.urls import reverse

from rest_framework.test import APIClient

import pytest
from faker import Faker

from libs.testing.constants import BAD_REQUEST, CREATED, NO_CONTENT

from ...api.serializers import (
    AttorneySerializer,
    ClientSerializer,
    SupportSerializer,
)
from ...models import AppUser, Attorney, Client, Support

fake = Faker()


@pytest.fixture(autouse=True)
def attorney_customer_mock(mocker):
    """Mock creation customer for attorney."""
    mock = mocker.patch(
        'apps.finance.models.CustomerProxy.create_with_payment_data'
    )
    yield mock


@pytest.fixture
def finance_profile_mock(mocker):
    """Mock creation finance profile for attorney."""
    mock = mocker.patch(
        'apps.finance.models.FinanceProfile.objects.create'
    )
    yield mock


@pytest.fixture(autouse=True)
def slug_related(mocker):
    """Mock calling drf `SlugRelatedField`."""
    mock = mocker.patch(
        'rest_framework.relations.SlugRelatedField.to_internal_value'
    )
    yield mock


def set_user_registration_data(data: dict, user: AppUser):
    """Fix registration data for AppUser model."""
    password = fake.password()
    data['password1'] = password
    data['password2'] = password
    data['email'] = fake.email()
    data['avatar'] = f'http://localhost{user.avatar.url}'


class TestAttorneyRegistration:
    """Test attorney registration."""

    @staticmethod
    def register_validation_url(stage: str):
        """Get url for attorney registration validation."""
        url = reverse('v1:attorneys-validate-registration')
        return f'{url}?stage={stage}'

    @property
    def register_url(self):
        """Get url for attorney registration."""
        return reverse('v1:attorneys-list')

    @staticmethod
    def set_registration_data(data: dict, attorney: Attorney):
        """Fix data json for successful registration."""
        set_user_registration_data(data=data, user=attorney.user)
        data['bar_number'] = fake.pyint(min_value=10000, max_value=90000)
        data['plan'] = 'plan_xxxxxxxxx777'
        data['payment_method'] = 'pmmm_xxxxxxxxx777'
        data['registration_attachments'] = [
            f'http://localhost{file_url}'
            for file_url in data['registration_attachments']
        ]

    def test_validate_registration_step_one_failed(
        self, api_client: APIClient, attorney: Attorney,
    ):
        """Check first stage of attorney validation."""
        validation_json = AttorneySerializer(instance=attorney).data

        url = self.register_validation_url(stage='first')
        response = api_client.post(url, validation_json)

        assert response.status_code == BAD_REQUEST

        # Check that api returned fields with invalid data
        assert 'email' in response.data['data']
        assert 'password1' in response.data['data']
        assert 'password2' in response.data['data']

    def test_validate_registration_step_one_success(
        self, api_client: APIClient, attorney: Attorney,
    ):
        """Check first stage of attorney validation on success."""
        data = AttorneySerializer(instance=attorney).data
        set_user_registration_data(data=data, user=attorney.user)

        url = self.register_validation_url(stage='first')

        response = api_client.post(url, data)

        assert response.status_code == NO_CONTENT

    def test_validate_registration_step_two_failed(
        self, api_client: APIClient, attorney: Attorney,
    ):
        """Check second stage of attorney validation."""
        validation_json = AttorneySerializer(instance=attorney).data

        # Set invalid data
        validation_json['education'] = []
        validation_json['practice_jurisdictions'] = []
        validation_json['specialities'] = []
        validation_json['fee_types'] = []
        validation_json['years_of_experience'] = -1

        url = self.register_validation_url(stage='second')
        response = api_client.post(url, validation_json)

        assert response.status_code == BAD_REQUEST

        # Check that api returned fields with invalid data
        assert 'avatar' in response.data['data']
        assert 'education' in response.data['data']
        assert 'practice_jurisdictions' in response.data['data']
        assert 'specialities' in response.data['data']
        assert 'fee_types' in response.data['data']
        assert 'years_of_experience' in response.data['data']

    def test_validate_registration_step_two_success(
        self, api_client: APIClient, attorney: Attorney,
    ):
        """Check second stage of attorney validation on success."""
        data = AttorneySerializer(instance=attorney).data
        self.set_registration_data(data=data, attorney=attorney)

        url = self.register_validation_url(stage='second')
        response = api_client.post(url, data)

        assert response.status_code == NO_CONTENT

    def test_registration(
        self, api_client: APIClient, attorney: Attorney, finance_profile_mock,
    ):
        """Test for create new Attorney through API.

        Should return HTTP 201 Created if attorney has been created
        successfully.

        """
        api_client.logout()

        data = AttorneySerializer(instance=attorney).data
        self.set_registration_data(data, attorney)
        response = api_client.post(self.register_url, data)

        assert response.status_code == CREATED
        # check that `finance_profile` was created
        assert finance_profile_mock.called

        # Check that new attorney appeared in db
        registered_attorney = Attorney.objects.get(pk=response.data['id'])

        # Check that attachments were saved
        attachments = set(attorney.registration_attachments.values_list(
            'attachment', flat=True
        ))
        registered_attachments = set(
            registered_attorney.registration_attachments.values_list(
                'attachment', flat=True
            )
        )
        # We checking here that there are no differences
        assert not attachments - registered_attachments


class TestClientRegistration:
    """Test client registration."""

    @property
    def register_url(self):
        """Get url for client registration."""
        return reverse('v1:clients-list')

    @staticmethod
    def fix_registration_data(data: dict, client: Client):
        """Fix data json for successful registration."""
        set_user_registration_data(data=data, user=client.user)

    def test_registration(self, api_client: APIClient, client: Client):
        """Test for create new Client through API.

        Should return HTTP 201 Created if client has been created
        successfully.

        """
        api_client.logout()

        data = ClientSerializer(instance=client).data
        self.fix_registration_data(data, client)
        response = api_client.post(self.register_url, data)

        assert response.status_code == CREATED

        # Check that new client appeared in db
        Client.objects.get(pk=response.data['id'])


class TestSupportRegistration:
    """Test support registration."""

    @property
    def register_url(self):
        """Get url for support registration."""
        return reverse('v1:support-list')

    @staticmethod
    def fix_registration_data(data: dict, support: Support):
        """Fix data json for successful registration."""
        set_user_registration_data(data=data, user=support.user)

    def test_registration(self, api_client: APIClient, support: Support):
        """Test for create new Support user through API.

        Should return HTTP 201 Created if supported user has been created
        successfully.

        """
        api_client.logout()

        data = SupportSerializer(instance=support).data
        self.fix_registration_data(data, support)
        response = api_client.post(self.register_url, data)

        assert response.status_code == CREATED

        # Check that new support appeared in db
        Support.objects.get(pk=response.data['id'])
