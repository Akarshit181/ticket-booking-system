import pytest
from fastapi import HTTPException

from app.models.token_model import LogoutRequest
from app.services import jwt_service


def test_logout_success(
    auth_service,
    refresh_token_repository,
    mocker,
):
    # Arrange
    request = LogoutRequest(
        refresh_token="refresh_token",
    )

    mocker.patch.object(
        jwt_service,
        "verify_token",
        return_value={"sub": "user123"},
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_token",
    )

    refresh_token_repository.find_by_token.return_value = {
        "user_id": "user123",
        "is_revoked": False,
    }

    # Act
    result = auth_service.logout(request)

    # Assert
    assert result == {"message": "Logged out successfully."}

    jwt_service.verify_token.assert_called_once_with(
        "refresh_token",
        token_type="refresh",
    )

    refresh_token_repository.find_by_token.assert_called_once_with("hashed_token")

    refresh_token_repository.revoke_for_logout.assert_called_once_with("hashed_token")


def test_logout_invalid_refresh_token(
    auth_service,
    mocker,
):
    # Arrange
    request = LogoutRequest(
        refresh_token="invalid_token",
    )

    mocker.patch.object(
        jwt_service,
        "verify_token",
        return_value=None,
    )

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.logout(request)

    assert exc_info.value.status_code == 401

    assert exc_info.value.detail == "Invalid or expired refresh token."


def test_logout_token_not_found(
    auth_service,
    refresh_token_repository,
    mocker,
):
    # Arrange
    request = LogoutRequest(
        refresh_token="refresh_token",
    )

    mocker.patch.object(
        jwt_service,
        "verify_token",
        return_value={"sub": "user123"},
    )

    mocker.patch.object(
        auth_service,
        "_hash_token",
        return_value="hashed_token",
    )

    refresh_token_repository.find_by_token.return_value = None

    # Act
    result = auth_service.logout(request)

    # Assert
    assert result == {"message": "Logged out successfully."}

    refresh_token_repository.find_by_token.assert_called_once_with("hashed_token")

    refresh_token_repository.revoke_for_logout.assert_not_called()


# logout()
#    │
#    ▼
# Verify JWT
#    │
#    ├── Invalid JWT ❌
#    │
#    ▼
# Find Refresh Token
#    │
#    ├── Exists
#    │      │
#    │      └── Revoke Token
#    │
#    └── Doesn't Exist
#           │
#           └── Return Success
