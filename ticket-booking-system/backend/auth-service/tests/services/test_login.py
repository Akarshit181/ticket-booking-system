import pytest
from fastapi import HTTPException

from app.models.user_model import UserLogin
from app.services import jwt_service, password_service


def test_login_user_success(
    auth_service,
    user_repository,
    refresh_token_repository,
    login_attempt_service,
    mocker,
):
    # Arrange
    user = UserLogin(
        email="john@example.com",
        password="Password@123",
    )

    existing_user = {
        "_id": "user123",
        "email": "john@example.com",
        "password_hash": "hashed_password",
        "role": "user",
        "is_active": True,
        "email_verified": True,
    }

    user_repository.get_by_email.return_value = existing_user
    login_attempt_service.is_blocked.return_value = False

    mock_verify = mocker.patch.object(
        password_service,
        "verify_password",
        return_value=True,
    )

    mock_access = mocker.patch.object(
        jwt_service,
        "create_access_token",
        return_value="access_token",
    )

    mock_refresh = mocker.patch.object(
        jwt_service,
        "create_refresh_token",
        return_value="refresh_token",
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_refresh_token",
    )

    # Act
    result = auth_service.login_user(user)

    # Assert
    assert result == {
        "access_token": "access_token",
        "refresh_token": "refresh_token",
        "token_type": "Bearer",
    }

    login_attempt_service.is_blocked.assert_called_once_with("john@example.com")

    user_repository.get_by_email.assert_called_once_with("john@example.com")

    mock_verify.assert_called_once_with(
        "Password@123",
        "hashed_password",
    )

    login_attempt_service.clear_attempts.assert_called_once_with("john@example.com")

    mock_access.assert_called_once()

    mock_refresh.assert_called_once()

    refresh_token_repository.save_refresh_token.assert_called_once()


def test_login_user_blocked(
    auth_service,
    login_attempt_service,
):
    # Arrange
    user = UserLogin(
        email="john@example.com",
        password="Password@123",
    )

    login_attempt_service.is_blocked.return_value = True

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.login_user(user)

    assert exc_info.value.status_code == 429
    assert (
        exc_info.value.detail
        == "Too many failed login attempts. Please try again later."
    )


def test_login_user_not_found(
    auth_service,
    user_repository,
    login_attempt_service,
):
    # Arrange
    user = UserLogin(
        email="john@example.com",
        password="Password@123",
    )

    login_attempt_service.is_blocked.return_value = False
    user_repository.get_by_email.return_value = None

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.login_user(user)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid email or password."

    login_attempt_service.record_failed_attempt.assert_called_once_with(
        "john@example.com"
    )


def test_login_user_invalid_password(
    auth_service,
    user_repository,
    login_attempt_service,
    mocker,
):
    # Arrange
    user = UserLogin(
        email="john@example.com",
        password="Password@123",
    )

    existing_user = {
        "_id": "user123",
        "email": "john@example.com",
        "password_hash": "hashed_password",
        "role": "user",
        "is_active": True,
        "email_verified": True,
    }

    login_attempt_service.is_blocked.return_value = False
    user_repository.get_by_email.return_value = existing_user

    mock_verify = mocker.patch.object(
        password_service,
        "verify_password",
        return_value=False,
    )

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.login_user(user)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid email or password."

    mock_verify.assert_called_once()

    login_attempt_service.record_failed_attempt.assert_called_once_with(
        "john@example.com"
    )


def test_login_user_inactive(
    auth_service,
    user_repository,
    login_attempt_service,
    mocker,
):
    # Arrange
    user = UserLogin(
        email="john@example.com",
        password="Password@123",
    )

    existing_user = {
        "_id": "user123",
        "email": "john@example.com",
        "password_hash": "hashed_password",
        "role": "user",
        "is_active": False,
        "email_verified": True,
    }

    login_attempt_service.is_blocked.return_value = False
    user_repository.get_by_email.return_value = existing_user

    mocker.patch.object(
        password_service,
        "verify_password",
        return_value=True,
    )

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.login_user(user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Account is disabled."

    login_attempt_service.clear_attempts.assert_not_called()


def test_login_user_email_not_verified(
    auth_service,
    user_repository,
    login_attempt_service,
    mocker,
):
    # Arrange
    user = UserLogin(
        email="john@example.com",
        password="Password@123",
    )

    existing_user = {
        "_id": "user123",
        "email": "john@example.com",
        "password_hash": "hashed_password",
        "role": "user",
        "is_active": True,
        "email_verified": False,
    }

    login_attempt_service.is_blocked.return_value = False
    user_repository.get_by_email.return_value = existing_user

    mocker.patch.object(
        password_service,
        "verify_password",
        return_value=True,
    )

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.login_user(user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Email verification required."

    login_attempt_service.clear_attempts.assert_not_called()
