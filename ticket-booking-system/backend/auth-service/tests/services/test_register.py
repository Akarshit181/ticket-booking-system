# A unit test verifies the business logic of a single unit in isolation.
import pytest
from types import SimpleNamespace
from fastapi import HTTPException
from app.models.user_model import UserRegister
from app.services import password_service


def test_register_user_success(
    auth_service,
    user_repository,
    email_verification_repository,
    notification_client,
    mocker,
):
    # Arrange
    user = UserRegister(
        username="john",
        email="john@example.com",
        password="Password@123",
    )

    user_repository.get_by_username.return_value = None
    user_repository.get_by_email.return_value = None

    created_user = SimpleNamespace(inserted_id="user123")
    user_repository.create.return_value = created_user

    # Everything returned by patch() is actually a MagicMock.It also remembers how many times it was called,
    # which arguments were passed  and in what order
    #     Inside the module password_service,

    # find the attribute named "hash_password"

    # replace it with a MagicMock.
    mock_hash = mocker.patch.object(
        password_service,
        "hash_password",
        return_value="hashed_password",
    )

    # Act
    result = auth_service.register_user(user)

    # Assert
    assert result == {"message": "User registered successfully."}

    user_repository.get_by_username.assert_called_once_with("john")

    user_repository.get_by_email.assert_called_once_with("john@example.com")

    mock_hash.assert_called_once_with("Password@123")

    user_repository.create.assert_called_once()

    email_verification_repository.save_verification_token.assert_called_once()

    notification_client.send_verification_email.assert_called_once()


def test_register_user_username_already_exists(
    auth_service,
    user_repository,
    email_verification_repository,
    notification_client,
    mocker,
):
    # Arrange
    user = UserRegister(
        username="john",
        email="john@example.com",
        password="Password@123",
    )

    # Pretend username already exists
    user_repository.get_by_username.return_value = {
        "_id": "user123",
        "username": "john",
    }

    mock_hash = mocker.patch.object(
        password_service,
        "hash_password",
        return_value="hashed_password",
    )

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.register_user(user)

    # Verify exception
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Username already exists."

    # Verify execution stopped
    user_repository.get_by_email.assert_not_called()
    mock_hash.assert_not_called()
    user_repository.create.assert_not_called()
    email_verification_repository.save_verification_token.assert_not_called()
    notification_client.send_verification_email.assert_not_called()


def test_register_user_email_already_exists(
    auth_service,
    user_repository,
    email_verification_repository,
    notification_client,
    mocker,
):
    # Arrange
    user = UserRegister(
        username="john",
        email="john@example.com",
        password="Password@123",
    )

    # Username is available
    user_repository.get_by_username.return_value = None

    # Email already exists
    user_repository.get_by_email.return_value = {
        "_id": "user123",
        "email": "john@example.com",
    }

    mock_hash = mocker.patch.object(
        password_service,
        "hash_password",
        return_value="hashed_password",
    )

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.register_user(user)

    # Verify exception
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Email already exists."

    # Verify flow
    user_repository.get_by_username.assert_called_once_with("john")
    user_repository.get_by_email.assert_called_once_with("john@example.com")

    mock_hash.assert_not_called()
    user_repository.create.assert_not_called()
    email_verification_repository.save_verification_token.assert_not_called()
    notification_client.send_verification_email.assert_not_called()


# Start pytest
#         │
#         ▼
# Read pytest.ini
#         │
#         ▼
# Load plugins
#         │
#         ▼
# Load conftest.py
#         │
#         ▼
# Create fixtures
# (auth_service,
# user_repository,
# notification_client...)
#         │
#         ▼
# Run test_register_user_success()
#         │
#         ▼
# Patch hash_password()
#         │
#         ▼
# Call auth_service.register_user()
#         │
#         ▼
# Check all assertions
#         │
#         ▼
# Everything correct
#         │
#         ▼
# PASS
