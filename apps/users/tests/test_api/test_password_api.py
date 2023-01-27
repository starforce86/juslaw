from django.core import mail
from django.urls import reverse

from rest_framework.test import APIClient

import pytest
from faker import Faker

from libs.testing.constants import BAD_REQUEST, OK

from ...models import AppUser

fake = Faker()


def get_password_reset_url():
    """Get url for password reset."""
    return reverse('v1:password_reset')


def get_password_change_url():
    """Get url for password change."""
    return reverse('v1:password_change')


@pytest.mark.parametrize(
    argnames='user',
    argvalues=(
        'client',
        'attorney'
    ),
    indirect=True
)
def test_password_reset(api_client: APIClient, user: AppUser):
    """Test that users can reset passwords.

    Should return HTTP 200 OK, because user with given email exists.

    """
    url = get_password_reset_url()
    data = {
        'email': user.email
    }
    response = api_client.post(url, data)

    assert response.status_code == OK

    # Check that email was delivered
    subject = '[example.com] Password Reset E-mail'
    filtered_inbox = [
        email for email in mail.outbox
        if email.subject == subject and email.to == [user.email]
    ]
    assert len(filtered_inbox) == 1


def test_password_invalid_reset(api_client: APIClient):
    """Test for password reset with invalid data.

    Should return HTTP 400 Bad request because fake email was provided.

    """
    url = get_password_reset_url()
    fake_email = fake.email()
    data = {
        'email': fake_email
    }
    response = api_client.post(url, data)

    assert response.status_code == BAD_REQUEST


@pytest.mark.parametrize(
    argnames='user',
    argvalues=(
        'client',
        'attorney'
    ),
    indirect=True
)
def test_password_change(api_client: APIClient, user: AppUser):
    """Test password change for users."""

    # Generate passwords for testing
    password_old = fake.password()
    user.set_password(password_old)
    user.save()
    password_new = fake.password()

    url = get_password_change_url()
    data = {
        'old_password': password_old,
        'new_password1': password_new,
        'new_password2': password_new
    }

    api_client.login(email=user.email, password=password_old)
    response = api_client.post(url, data)
    assert response.status_code == OK
    api_client.logout()

    # Check that old password won't work, and user must use new password
    assert not api_client.login(email=user.email, password=password_old)
    assert api_client.login(email=user.email, password=password_new)


@pytest.mark.parametrize(
    argnames='user',
    argvalues=(
        'client',
        'attorney'
    ),
    indirect=True
)
def test_password_change_wrong_password(api_client: APIClient, user: AppUser):
    """Test for password change with wrong password."""
    password_old = fake.password()
    user.set_password(password_old)
    user.save()
    password_new = fake.password()

    url = get_password_change_url()
    data = {
        'old_password': password_new,
        'new_password1': password_new,
        'new_password2': password_new
    }

    api_client.login(email=user.email, password=password_old)
    response = api_client.post(url, data)
    assert response.status_code == BAD_REQUEST
