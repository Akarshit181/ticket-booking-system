import pytest
from types import SimpleNamespace
from fastapi import HTTPException

from app.models.token_model import RefreshTokenRequest, TokenResponse
from app.services import jwt_service


def test_refresh_access_token_success(
    auth_service,
    user_repository,
    refresh_token_repository,
    mocker,
):
    # Arrange
    request = RefreshTokenRequest(refresh_token="old_refresh_token")

    token_payload = SimpleNamespace(
        sub="user123",
        email="john@example.com",
        role="user",
    )

    existing_refresh_token = {
        "user_id": "user123",
        "is_revoked": False,
    }

    existing_user = {
        "_id": "user123",
        "email": "john@example.com",
        "role": "user",
        "is_active": True,
        "email_verified": True,
    }

    mocker.patch.object(
        jwt_service,
        "verify_token",
        return_value=token_payload,
    )

    mock_hash = mocker.patch.object(
        auth_service,
        "_hash_token",
        side_effect=[
            "old_hash",
            "new_hash",
        ],
    )

    user_repository.get_by_id.return_value = existing_user

    refresh_token_repository.find_by_token.return_value = existing_refresh_token

    mock_access = mocker.patch.object(
        jwt_service,
        "create_access_token",
        return_value="new_access_token",
    )

    mock_refresh = mocker.patch.object(
        jwt_service,
        "create_refresh_token",
        return_value="new_refresh_token",
    )

    refresh_token_repository.consume_for_rotation.return_value = {"_id": "token1"}

    mock_save = mocker.patch.object(
        auth_service,
        "_save_refresh_token",
    )

    # Act
    result = auth_service.refresh_access_token(request)

    # Assert

    assert isinstance(result, TokenResponse)

    assert result.access_token == "new_access_token"

    assert result.refresh_token == "new_refresh_token"

    assert result.token_type == "bearer"

    jwt_service.verify_token.assert_called_once_with(
        "old_refresh_token",
        token_type="refresh",
    )

    assert mock_hash.call_count == 2

    refresh_token_repository.find_by_token.assert_called_once_with("old_hash")

    user_repository.get_by_id.assert_called_once_with("user123")

    mock_access.assert_called_once()

    mock_refresh.assert_called_once()

    refresh_token_repository.consume_for_rotation.assert_called_once_with(
        "old_hash",
        "new_hash",
    )

    mock_save.assert_called_once_with(
        "user123",
        "new_refresh_token",
    )


def test_refresh_access_token_invalid_jwt(
    auth_service,
    mocker,
):
    # Arrange
    request = RefreshTokenRequest(refresh_token="invalid_token")

    mocker.patch.object(
        jwt_service,
        "verify_token",
        return_value=None,
    )

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.refresh_access_token(request)

    assert exc_info.value.status_code == 401

    assert exc_info.value.detail == "Invalid or expired refresh token."


def test_refresh_access_token_token_not_found(
    auth_service,
    refresh_token_repository,
    mocker,
):
    # Arrange
    request = RefreshTokenRequest(refresh_token="refresh_token")

    token_payload = SimpleNamespace(
        sub="user123",
    )

    mocker.patch.object(
        jwt_service,
        "verify_token",
        return_value=token_payload,
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_token",
    )

    refresh_token_repository.find_by_token.return_value = None

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.refresh_access_token(request)

    assert exc_info.value.status_code == 401

    assert exc_info.value.detail == "Invalid or expired refresh token."

    refresh_token_repository.find_by_token.assert_called_once_with("hashed_token")


def test_refresh_access_token_revoked(
    auth_service,
    refresh_token_repository,
    mocker,
):
    # Arrange
    request = RefreshTokenRequest(refresh_token="refresh_token")

    token_payload = SimpleNamespace(
        sub="user123",
    )

    revoked_token = {
        "user_id": "user123",
        "is_revoked": True,
        "revocation_reason": "rotation",
    }

    mocker.patch.object(
        jwt_service,
        "verify_token",
        return_value=token_payload,
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_token",
    )

    refresh_token_repository.find_by_token.return_value = revoked_token

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.refresh_access_token(request)

    assert exc_info.value.status_code == 401

    assert exc_info.value.detail == "Invalid or expired refresh token."

    refresh_token_repository.revoke_all_by_user_id.assert_called_once_with("user123")


def test_refresh_access_token_user_not_found(
    auth_service,
    user_repository,
    refresh_token_repository,
    mocker,
):
    # Arrange
    request = RefreshTokenRequest(
        refresh_token="refresh_token",
    )

    token_payload = SimpleNamespace(
        sub="user123",
    )

    refresh_token = {
        "user_id": "user123",
        "is_revoked": False,
    }

    mocker.patch.object(
        jwt_service,
        "verify_token",
        return_value=token_payload,
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_token",
    )

    refresh_token_repository.find_by_token.return_value = refresh_token

    user_repository.get_by_id.return_value = None

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.refresh_access_token(request)

    assert exc_info.value.status_code == 401

    assert exc_info.value.detail == "Invalid refresh token."

    refresh_token_repository.revoke_all_by_user_id.assert_called_once_with("user123")


def test_refresh_access_token_user_inactive(
    auth_service,
    user_repository,
    refresh_token_repository,
    mocker,
):
    # Arrange
    request = RefreshTokenRequest(
        refresh_token="refresh_token",
    )

    token_payload = SimpleNamespace(
        sub="user123",
    )

    refresh_token = {
        "user_id": "user123",
        "is_revoked": False,
    }

    user = {
        "_id": "user123",
        "email": "john@example.com",
        "role": "user",
        "is_active": False,
        "email_verified": True,
    }

    mocker.patch.object(
        jwt_service,
        "verify_token",
        return_value=token_payload,
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_token",
    )

    refresh_token_repository.find_by_token.return_value = refresh_token

    user_repository.get_by_id.return_value = user

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.refresh_access_token(request)

    assert exc_info.value.status_code == 403

    assert exc_info.value.detail == "Account is disabled."

    refresh_token_repository.revoke_all_by_user_id.assert_called_once_with("user123")


def test_refresh_access_token_email_not_verified(
    auth_service,
    user_repository,
    refresh_token_repository,
    mocker,
):
    # Arrange
    request = RefreshTokenRequest(
        refresh_token="refresh_token",
    )

    token_payload = SimpleNamespace(
        sub="user123",
    )

    refresh_token = {
        "user_id": "user123",
        "is_revoked": False,
    }

    user = {
        "_id": "user123",
        "email": "john@example.com",
        "role": "user",
        "is_active": True,
        "email_verified": False,
    }

    mocker.patch.object(
        jwt_service,
        "verify_token",
        return_value=token_payload,
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_token",
    )

    refresh_token_repository.find_by_token.return_value = refresh_token

    user_repository.get_by_id.return_value = user

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.refresh_access_token(request)

    assert exc_info.value.status_code == 403

    assert exc_info.value.detail == "Email verification required."

    refresh_token_repository.revoke_all_by_user_id.assert_called_once_with("user123")


def test_refresh_access_token_rotation_failed(
    auth_service,
    user_repository,
    refresh_token_repository,
    mocker,
):
    # Arrange
    request = RefreshTokenRequest(
        refresh_token="old_refresh_token",
    )

    token_payload = SimpleNamespace(
        sub="user123",
        email="john@example.com",
        role="user",
    )

    refresh_token = {
        "user_id": "user123",
        "is_revoked": False,
    }

    user = {
        "_id": "user123",
        "email": "john@example.com",
        "role": "user",
        "is_active": True,
        "email_verified": True,
    }

    mocker.patch.object(
        jwt_service,
        "verify_token",
        return_value=token_payload,
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        side_effect=[
            "old_hash",
            "new_hash",
        ],
    )

    refresh_token_repository.find_by_token.return_value = refresh_token

    user_repository.get_by_id.return_value = user

    mocker.patch.object(
        jwt_service,
        "create_access_token",
        return_value="access_token",
    )

    mocker.patch.object(
        jwt_service,
        "create_refresh_token",
        return_value="new_refresh_token",
    )

    refresh_token_repository.consume_for_rotation.return_value = None

    mock_save = mocker.patch.object(
        auth_service,
        "_save_refresh_token",
    )

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.refresh_access_token(request)

    assert exc_info.value.status_code == 401

    assert exc_info.value.detail == "Invalid or expired refresh token."

    refresh_token_repository.consume_for_rotation.assert_called_once_with(
        "old_hash",
        "new_hash",
    )

    refresh_token_repository.revoke_all_by_user_id.assert_called_once_with("user123")

    mock_save.assert_not_called()


# Refresh Request
#       │
#       ▼
# Verify JWT
#       │
#       ├── Invalid JWT ❌
#       │
#       ▼
# Find Refresh Token
#       │
#       ├── Not Found ❌
#       │
#       ▼
# Revoked?
#       │
#       ├── Yes (rotation?)
#       │         │
#       │         ├── revoke_all_by_user_id()
#       │         └── HTTPException
#       │
#       ▼
# Find User
#       │
#       ├── Not Found ❌
#       │
#       ▼
# User Active?
#       │
#       ├── No ❌
#       │
#       ▼
# Email Verified?
#       │
#       ├── No ❌
#       │
#       ▼
# Create New Tokens
#       │
#       ▼
# Rotate Token
#       │
#       ├── Failed ❌
#       │
#       ▼
# Save New Refresh Token
#       │
#       ▼
# Return Tokens ✅
